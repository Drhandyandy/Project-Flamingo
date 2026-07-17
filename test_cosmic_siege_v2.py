#!/usr/bin/env python3
"""
Unit tests for Cosmic Siege Engine v2.0
Tests key recovery, address derivation, and database operations.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cosmic_siege_engine_v2 import (
    recover_private_key_from_nonce_reuse,
    modinv,
    N,
    P,
    point_x_from_private,
    private_to_wif,
    verify_key,
    pubkey_hex_from_private,
    init_db,
    save_recovered_key,
    get_all_recovered_keys,
    detect_nonce_reuse
)


class TestNonceReuseRecovery(unittest.TestCase):
    """Test cases for nonce reuse key recovery."""
    
    def test_basic_nonce_reuse_recovery(self):
        """Test basic nonce reuse recovery with known values."""
        d_true = 12345678901234567890
        k_nonce = 98765432109876543210
        z1 = 11111111111111111111
        z2 = 22222222222222222222
        
        r = point_x_from_private(k_nonce)
        s1 = (modinv(k_nonce, N) * (z1 + r * d_true)) % N
        s2 = (modinv(k_nonce, N) * (z2 + r * d_true)) % N
        
        d_recovered = recover_private_key_from_nonce_reuse(r, s1, s2, z1, z2)
        
        self.assertIsNotNone(d_recovered)
        self.assertEqual(d_recovered, d_true)
    
    def test_large_values_recovery(self):
        """Test recovery with full 256-bit values."""
        d_true = 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
        k_nonce = 0xfedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321
        z1 = 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        z2 = 0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
        
        r = point_x_from_private(k_nonce)
        s1 = (modinv(k_nonce, N) * (z1 + r * d_true)) % N
        s2 = (modinv(k_nonce, N) * (z2 + r * d_true)) % N
        
        d_recovered = recover_private_key_from_nonce_reuse(r, s1, s2, z1, z2)
        
        self.assertIsNotNone(d_recovered)
        self.assertEqual(d_recovered, d_true)
    
    def test_invalid_same_s_values(self):
        """Test that recovery fails when s1 == s2."""
        r = 0x1234567890abcdef
        s1 = 0xabcdef1234567890
        s2 = 0xabcdef1234567890  # Same as s1
        z1 = 0x1111111111111111
        z2 = 0x2222222222222222
        
        d_recovered = recover_private_key_from_nonce_reuse(r, s1, s2, z1, z2)
        
        self.assertIsNone(d_recovered)


class TestModularInverse(unittest.TestCase):
    """Test modular inverse calculations."""
    
    def test_modinv_basic(self):
        """Test basic modular inverse."""
        a = 12345
        inv = modinv(a, N)
        result = (a * inv) % N
        self.assertEqual(result, 1)
    
    def test_modinv_zero(self):
        """Test that modinv raises error for zero."""
        with self.assertRaises(ValueError):
            modinv(0, N)


class TestKeyDerivation(unittest.TestCase):
    """Test key derivation functions."""
    
    def test_private_to_wif_compressed(self):
        """Test WIF conversion for compressed key."""
        d = 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
        wif = private_to_wif(d, compressed=True)
        self.assertTrue(wif.startswith('L') or wif.startswith('K'))
        self.assertEqual(len(wif), 52)
    
    def test_private_to_wif_uncompressed(self):
        """Test WIF conversion for uncompressed key."""
        d = 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
        wif = private_to_wif(d, compressed=False)
        self.assertTrue(wif.startswith('5'))
        self.assertEqual(len(wif), 51)
    
    def test_verify_key_valid(self):
        """Test key verification with valid key."""
        d = 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
        pubkey_hex = pubkey_hex_from_private(d)
        self.assertTrue(verify_key(d, pubkey_hex))
    
    def test_pubkey_hex_consistency(self):
        """Test that pubkey hex is consistent."""
        d = 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
        pubkey1 = pubkey_hex_from_private(d, compressed=True)
        pubkey2 = pubkey_hex_from_private(d, compressed=True)
        self.assertEqual(pubkey1, pubkey2)


class TestNonceReuseDetection(unittest.TestCase):
    """Test nonce reuse detection from signatures."""
    
    def test_detect_reuse_with_same_r(self):
        """Test detection of nonce reuse with same r value."""
        sig1 = {'r': 0x1234, 's': 0x5678, 'txid': 'tx1'}
        sig2 = {'r': 0x1234, 's': 0x9abc, 'txid': 'tx2'}  # Same r
        sig3 = {'r': 0x5678, 's': 0xdef0, 'txid': 'tx3'}  # Different r
        
        signatures = [sig1, sig2, sig3]
        pairs = detect_nonce_reuse(signatures)
        
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0]['r'], pairs[0][1]['r'])
    
    def test_no_reuse_different_r(self):
        """Test no false positives when all r values differ."""
        sig1 = {'r': 0x1234, 's': 0x5678, 'txid': 'tx1'}
        sig2 = {'r': 0x5678, 's': 0x9abc, 'txid': 'tx2'}
        sig3 = {'r': 0x9abc, 's': 0xdef0, 'txid': 'tx3'}
        
        signatures = [sig1, sig2, sig3]
        pairs = detect_nonce_reuse(signatures)
        
        self.assertEqual(len(pairs), 0)
    
    def test_multiple_reuse_pairs(self):
        """Test detection of multiple nonce reuse pairs."""
        sig1 = {'r': 0x1111, 's': 0x2222, 'txid': 'tx1'}
        sig2 = {'r': 0x1111, 's': 0x3333, 'txid': 'tx2'}
        sig3 = {'r': 0x4444, 's': 0x5555, 'txid': 'tx3'}
        sig4 = {'r': 0x4444, 's': 0x6666, 'txid': 'tx4'}
        
        signatures = [sig1, sig2, sig3, sig4]
        pairs = detect_nonce_reuse(signatures)
        
        self.assertEqual(len(pairs), 2)


class TestDatabaseOperations(unittest.TestCase):
    """Test database operations."""
    
    @classmethod
    def setUpClass(cls):
        """Initialize database before tests."""
        init_db()
    
    def test_save_and_retrieve_key(self):
        """Test saving and retrieving a recovered key."""
        d = 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
        address = "test_address_123"
        pubkey_hex = "test_pubkey_456"
        
        success = save_recovered_key(address, d, pubkey_hex, 
                                    recovery_method="test", verified=True)
        self.assertTrue(success)
        
        keys = get_all_recovered_keys()
        self.assertIsInstance(keys, list)
    
    def test_get_empty_keys(self):
        """Test retrieving keys when database is empty."""
        keys = get_all_recovered_keys()
        self.assertIsInstance(keys, list)


if __name__ == '__main__':
    unittest.main(verbosity=2)
