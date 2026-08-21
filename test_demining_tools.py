#!/usr/bin/env python3
"""
Unit tests for demining_tools.py (Demining Suite).
"""

import os
import json
import tempfile
import secrets
import pytest

from crypto_utils import N, G, scalar_mul, mod_inv, derive_address
from demining_tools import (
    MineDetector, DeminingRig,
    RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL,
    FLAMINGO_SCALE, FLAMINGO_C
)


def test_repeated_nonce_mine_detection():
    """Test detection of repeated nonces and key recovery."""
    k_mine = secrets.randbits(256) % N
    d_true = secrets.randbits(256) % N
    z1 = secrets.randbits(256) % N
    z2 = secrets.randbits(256) % N

    R_pt = scalar_mul(k_mine, G)
    r_val = R_pt[0] % N
    s1 = (mod_inv(k_mine, N) * (z1 + r_val * d_true)) % N
    s2 = (mod_inv(k_mine, N) * (z2 + r_val * d_true)) % N

    sigs = [
        {'r': r_val, 's': s1, 'z': z1},
        {'r': r_val, 's': s2, 'z': z2}
    ]

    hazards = MineDetector.check_signature_nonce_reuse(sigs)
    assert len(hazards) == 1
    assert hazards[0]['type'] == 'REPEATED_NONCE_MINE'
    assert hazards[0]['risk_level'] == RISK_CRITICAL
    assert int(hazards[0]['recovered_key'], 16) == d_true


def test_no_nonce_reuse():
    """Test clean signatures without nonce reuse."""
    sigs = [
        {'r': 12345, 's': 67890, 'z': 11111},
        {'r': 54321, 's': 98765, 'z': 22222}
    ]

    hazards = MineDetector.check_signature_nonce_reuse(sigs)
    assert len(hazards) == 0


def test_flamingo_polynomial_bias_detection():
    """Test detection of Flamingo polynomial nonce bias."""
    d_true = secrets.randbits(256) % N
    sigs = []

    for n in range(1, 4):
        k = FLAMINGO_SCALE * (10 * n * n + 2)
        z = secrets.randbits(256) % N
        R_pt = scalar_mul(k, G)
        r = R_pt[0] % N
        s = (mod_inv(k, N) * (z + r * d_true)) % N
        sigs.append({'r': r, 's': s, 'z': z})

    poly_hazard = MineDetector.check_flamingo_polynomial_bias(sigs, max_n=50)
    assert poly_hazard is not None
    assert poly_hazard['type'] == 'FLAMINGO_POLYNOMIAL_BIAS_MINE'
    assert int(poly_hazard['recovered_key'], 16) == d_true


def test_small_nonce_bias_detection():
    """Test detection of small nonces (k < 2^160, e.g. SHA-1 nonces / truncated RNG)."""
    sigs = [
        {'r': 12345, 's': 67890, 'z': 11111, 'k': 0x1234567890abcdef12345678},
        {'r': 54321, 's': 98765, 'z': 22222, 'k': secrets.randbits(256)}
    ]

    hazards = MineDetector.check_small_nonce_bias(sigs, max_k_bits=160)
    assert len(hazards) == 1
    assert hazards[0]['type'] == 'SMALL_NONCE_BIAS_MINE'
    assert hazards[0]['risk_level'] == RISK_CRITICAL


def test_invalid_generator_curveball_trap():
    """Test detection of CurveBall generator trap (G' = Pubkey P)."""
    d_dummy = 123456789
    pub_pt = scalar_mul(d_dummy, G)

    cb_hazard = MineDetector.check_invalid_generator_trap(pubkey_point=pub_pt, custom_generator=pub_pt)
    assert cb_hazard['hazard'] == 'CURVEBALL_GENERATOR_TRAP'
    assert cb_hazard['risk_level'] == RISK_CRITICAL

    clean_check = MineDetector.check_invalid_generator_trap(pubkey_point=pub_pt, custom_generator=G)
    assert clean_check['hazard'] is None
    assert clean_check['risk_level'] == RISK_LOW


def test_backdoor_key_offset_audit():
    """Test auditing for structured constant offset backdoor."""
    c_inv = mod_inv(FLAMINGO_C, N)
    offset = 384
    d_backdoored = (N - offset * FLAMINGO_C) % N

    audit = MineDetector.check_key_backdoor_offset(d_backdoored)
    assert audit['is_backdoored'] is True
    assert audit['risk_level'] == RISK_CRITICAL

    d_clean = secrets.randbits(256) % N
    audit_clean = MineDetector.check_key_backdoor_offset(d_clean)
    assert audit_clean['is_backdoored'] is False


def test_utxo_script_hazards():
    """Test scanning UTXO scripts for dust, timelocks, and unspendable opcodes."""
    # Standard P2PKH
    res_std = MineDetector.scan_utxo_script("76a9140088ac", 50000)
    assert res_std['risk_level'] == RISK_LOW
    assert res_std['safe_to_spend'] is True

    # Dust
    res_dust = MineDetector.scan_utxo_script("76a9140088ac", 300)
    assert res_dust['risk_level'] == RISK_HIGH
    assert res_dust['safe_to_spend'] is False
    assert any(h['hazard'] == 'DUST_TRAP' for h in res_dust['hazards'])

    # OP_RETURN
    res_op = MineDetector.scan_utxo_script("6a140011223344", 10000)
    assert res_op['risk_level'] == RISK_CRITICAL
    assert res_op['safe_to_spend'] is False
    assert any(h['hazard'] == 'UNSPENDABLE_OP_RETURN' for h in res_op['hazards'])

    # Timelock
    res_time = MineDetector.scan_utxo_script("63b17521", 200000)
    assert res_time['risk_level'] == RISK_HIGH
    assert any(h['hazard'] == 'TIMELOCK_TRAP' for h in res_time['hazards'])


def test_assess_frontrun_risk():
    """Test mempool frontrun risk assessment."""
    risk_normal = MineDetector.assess_frontrun_risk(
        mempool_fee_rate_sat_vb=10.0,
        tx_vbytes=192,
        output_value_sats=100000
    )
    assert risk_normal['anti_frontrun_fee_rate_sat_vb'] == 35.0
    assert risk_normal['net_sweep_value_sats'] > 0

    risk_low_val = MineDetector.assess_frontrun_risk(
        mempool_fee_rate_sat_vb=20.0,
        tx_vbytes=192,
        output_value_sats=1000
    )
    assert risk_low_val['risk_level'] == RISK_CRITICAL


def test_build_safe_sweep_payload():
    """Test anti-frontrunning sweep transaction payload generator."""
    rig = DeminingRig()
    d_hex = "0x1122334455667788990011223344556677889900112233445566778899001122"
    src_addr = derive_address(int(d_hex, 16), compressed=True)
    dst_addr = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

    payload = rig.build_safe_sweep_payload(
        private_key_hex=d_hex,
        source_address=src_addr,
        destination_address=dst_addr,
        utxo_amount_sats=200000,
        mempool_fee_rate=10.0,
        anti_frontrun=True
    )

    assert payload['status'] == 'READY'
    assert payload['source_address'] == src_addr
    assert payload['destination_address'] == dst_addr
    assert payload['sweep_amount_sats'] < 200000
    assert payload['fee_sats'] > 0


def test_batch_demine_file():
    """Test batch processing of signature records from CSV."""
    rig = DeminingRig()

    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.csv', newline='') as f_in:
        input_path = f_in.name
        f_in.write("address,txid,r,s,z\n")
        f_in.write("1Addr1,tx1,0x1111,0x2222,0x3333\n")
        f_in.write("1Addr1,tx2,0x1111,0x4444,0x5555\n")  # Nonce reuse hazard on 1Addr1
        f_in.write("1Addr2,tx3,0x7777,0x8888,0x9999\n")

    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as f_out:
        output_path = f_out.name

    try:
        summary = rig.batch_demine_file(input_path, output_path)
        assert summary['total_records_scanned'] == 3
        assert summary['unique_addresses'] == 2
        assert summary['compromised_addresses'] == 1
        assert os.path.exists(output_path)
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


if __name__ == '__main__':
    pytest.main([__file__])
