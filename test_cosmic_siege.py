#!/usr/bin/env python3
"""
Test suite for cosmic_siege_engine.py
Validates core functionality without external dependencies.
"""

import sys
import hashlib
import base58
from typing import Tuple

# Import the functions we want to test
try:
    from cosmic_siege_engine import (
        modinv, private_to_wif, verify_key, 
        recover_private_key_from_nonce_reuse,
        N
    )
except ImportError as e:
    print(f"[ERROR] Cannot import cosmic_siege_engine: {e}")
    sys.exit(1)


def test_modinv() -> bool:
    """Test modular inverse computation."""
    print("\n[TEST] Modular Inverse (modinv)")
    
    # Test: modinv(5, N) * 5 ≡ 1 (mod N)
    a = 5
    inv = modinv(a, N)
    result = (a * inv) % N
    
    passed = result == 1
    print(f"  modinv(5, N) * 5 mod N = {result}")
    print(f"  Expected: 1")
    print(f"  Status: {'✓ PASS' if passed else '✗ FAIL'}")
    
    return passed


def test_private_to_wif() -> bool:
    """Test WIF encoding."""
    print("\n[TEST] Private Key to WIF Conversion")
    
    # Test with known value
    d = 0x0a0a14bad3813ec45fe182cfab24bfb9bee10db4c709595e6bd19f755aa41d14
    wif_compressed = private_to_wif(d, compressed=True)
    wif_uncompressed = private_to_wif(d, compressed=False)
    
    # Expected values from the notebook
    expected_compressed = "KwZE4vjSMXRdyvQ9B9iJKejwpDJ8jiNiepHVRYpxL61stgjbVk53"
    expected_uncompressed = "5Hti2LsrFAcVKLMCNLCApGoS7Aanhwgp3gG4ip5yVLiS8D1GUHq"
    
    passed = wif_compressed == expected_compressed and wif_uncompressed == expected_uncompressed
    
    print(f"  Input (hex): {d:064x}")
    print(f"  WIF (compressed):   {wif_compressed}")
    print(f"  Expected:           {expected_compressed}")
    print(f"  WIF (uncompressed): {wif_uncompressed}")
    print(f"  Expected:           {expected_uncompressed}")
    print(f"  Status: {'✓ PASS' if passed else '✗ FAIL'}")
    
    return passed


def test_nonce_reuse_recovery() -> bool:
    """Test ECDSA nonce reuse recovery algorithm."""
    print("\n[TEST] ECDSA Nonce Reuse Recovery")
    
    # Use known values from notebook demonstration
    d_true = 0x0a0a14bad3813ec45fe182cfab24bfb9bee10db4c709595e6bd19f755aa41d14
    
    # Synthetic values for testing
    r = 0x12345678900000000000000000000000000000000000000000000000000000ab
    s1 = 0x87654321900000000000000000000000000000000000000000000000000000cd
    s2 = 0x87654321800000000000000000000000000000000000000000000000000000ce
    z1 = 0xaabbccdd00000000000000000000000000000000000000000000000000000001
    z2 = 0xaabbccdd00000000000000000000000000000000000000000000000000000002
    
    # Manually compute recovery to test the algorithm
    s_diff = (s1 - s2) % N
    k_recovered = ((z1 - z2) * modinv(s_diff, N)) % N
    d_recovered = ((k_recovered * s1 - z1) * modinv(r, N)) % N
    
    # Test the function
    result = recover_private_key_from_nonce_reuse(r, s1, s2, z1, z2)
    
    passed = result == d_recovered
    
    print(f"  True private key:     0x{d_true:064x}")
    print(f"  Recovered key:        0x{result:064x}")
    print(f"  Manual calculation:   0x{d_recovered:064x}")
    print(f"  Match: {result == d_recovered}")
    print(f"  Status: {'✓ PASS' if passed else '✗ FAIL'}")
    
    return passed


def test_basic_secp256k1_math() -> bool:
    """Test basic secp256k1 constants and operations."""
    print("\n[TEST] Basic SECP256K1 Math")
    
    # Test that N is the correct order
    # N should be approximately 2^256
    bit_length = N.bit_length()
    passed = bit_length == 256
    
    print(f"  Curve Order (N) bit length: {bit_length}")
    print(f"  Expected: 256")
    print(f"  N = 0x{N:064x}")
    print(f"  Status: {'✓ PASS' if passed else '✗ FAIL'}")
    
    return passed


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 80)
    print("COSMIC SIEGE ENGINE - TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("SECP256K1 Constants", test_basic_secp256k1_math),
        ("Modular Inverse", test_modinv),
        ("WIF Encoding", test_private_to_wif),
        ("Nonce Reuse Recovery", test_nonce_reuse_recovery),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[ERROR] Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:<30} {status}")
    
    print("-" * 80)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
