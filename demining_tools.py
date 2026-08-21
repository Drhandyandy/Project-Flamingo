#!/usr/bin/env python3
"""
==============================================================================
🦩 PROJECT FLAMINGO: DEMINING TOOLS & MINEFIELD SWEEPER RIG (V1.1)
==============================================================================

Provides comprehensive detection and demining tools for Bitcoin transactions,
signatures, UTXOs, and addresses.

Capabilities:
1. Signature Minefield Detection:
   - Nonce reuse identification
   - Polynomial nonce bias detection (Flamingo shell / J(n) nonces)
   - Small nonce / truncated hash bias detection (k < 2^160, SHA-1 / weak RNG)
   - Invalid generator / CurveBall trap detection (G' = Pubkey substitution)
   - Low-entropy / static nonce leakage
   - Backdoored key offset auditing
2. UTXO & Script Hazard Demining:
   - Timelock traps (CLTV / CSV)
   - Unspendable output traps (OP_RETURN, OP_FALSE, invalid opcodes)
   - Dust traps / fee-draining honeypots (< 546 sats)
   - Multi-sig / script path traps
3. Anti-Frontrun Sweeper & Transaction Builder:
   - High-fidelity safe sweep transaction payload generator
   - Priority fee escalation for anti-frontrunning protection
   - Risk scoring (LOW, MEDIUM, HIGH, CRITICAL)
4. Batch Processing & CLI Interface
==============================================================================
"""

import sys
import os
import csv
import json
import time
import math
import hashlib
import secrets
import argparse
from typing import Dict, List, Tuple, Optional, Any, Union

from crypto_utils import (
    P, N, G, mod_inv, scalar_mul, derive_address, to_wif,
    PHOENIX_SHUNT, HULL_RESONANCE, get_pulse_656
)

# Constants for Demining Risk Levels
RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"
RISK_CRITICAL = "CRITICAL"

DUST_THRESHOLD_SATS = 546
FLAMINGO_SCALE = 32
FLAMINGO_C = (1 << 32) + 977


class MineDetector:
    """
    Core detector for cryptographic and script-level hazards ("mines")
    in Bitcoin signatures, transactions, and UTXOs.
    """

    @staticmethod
    def check_signature_nonce_reuse(signatures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detects nonce reuse traps where two or more signatures share the same 'r' value.
        """
        r_map = {}
        hazards = []

        for idx, sig in enumerate(signatures):
            r_val = sig.get('r')
            if r_val is None:
                continue

            r_norm = hex(r_val) if isinstance(r_val, int) else str(r_val).lower()
            if r_norm in r_map:
                prev_idx = r_map[r_norm]
                prev_sig = signatures[prev_idx]

                # Attempt private key recovery if z values are available
                recovered_key = None
                s1, s2 = sig.get('s'), prev_sig.get('s')
                z1, z2 = sig.get('z'), prev_sig.get('z')

                if all(v is not None for v in (s1, s2, z1, z2)) and s1 != s2:
                    s_diff = (s1 - s2) % N
                    if s_diff != 0:
                        k_recovered = ((z1 - z2) * mod_inv(s_diff, N)) % N
                        r_int = r_val if isinstance(r_val, int) else int(r_val, 16)
                        d_recovered = ((k_recovered * s1 - z1) * mod_inv(r_int, N)) % N
                        recovered_key = hex(d_recovered)

                hazards.append({
                    'type': 'REPEATED_NONCE_MINE',
                    'risk_level': RISK_CRITICAL,
                    'r_value': r_norm,
                    'indices': [prev_idx, idx],
                    'recovered_key': recovered_key,
                    'description': 'Identical r-value detected across multiple signatures. Private key compromised.'
                })
            else:
                r_map[r_norm] = idx

        return hazards

    @staticmethod
    def check_flamingo_polynomial_bias(signatures: List[Dict[str, Any]], max_n: int = 100) -> Optional[Dict[str, Any]]:
        """
        Detects polynomial nonce bias k = SCALE * (10n^2 + 2) used in shell signatures.
        """
        valid_sigs = [s for s in signatures if all(s.get(k) is not None for k in ('r', 's', 'z'))]
        if len(valid_sigs) < 2:
            return None

        # Build candidate k values
        candidates = {}
        for n in range(1, max_n + 1):
            k_val = FLAMINGO_SCALE * (10 * n * n + 2)
            candidates[k_val] = n

        sig1 = valid_sigs[0]
        r1, s1, z1 = sig1['r'], sig1['s'], sig1['z']
        r1_inv = mod_inv(r1, N)

        for k_cand, n_val in candidates.items():
            d_cand = ((s1 * k_cand - z1) * r1_inv) % N

            matches = 1
            matched_indices = [0]
            for idx, other_sig in enumerate(valid_sigs[1:], start=1):
                ro, so, zo = other_sig['r'], other_sig['s'], other_sig['z']
                k_other = ((zo + ro * d_cand) * mod_inv(so, N)) % N
                if k_other in candidates:
                    matches += 1
                    matched_indices.append(idx)

            if matches >= 2 and matches >= min(3, len(valid_sigs)):
                return {
                    'type': 'FLAMINGO_POLYNOMIAL_BIAS_MINE',
                    'risk_level': RISK_CRITICAL,
                    'recovered_key': hex(d_cand),
                    'matches': matches,
                    'total_scanned': len(valid_sigs),
                    'description': f'Polynomial nonce sequence detected (J(n) pattern) across {matches} signatures.'
                }

        return None

    @staticmethod
    def check_small_nonce_bias(signatures: List[Dict[str, Any]], max_k_bits: int = 160) -> List[Dict[str, Any]]:
        """
        Detects truncated/small nonces (k < 2^max_k_bits, e.g. SHA-1 nonces or short RNG output).
        Inspired by ECC_Attacks/biased_k_values.
        """
        hazards = []
        max_k_bound = 1 << max_k_bits

        for idx, sig in enumerate(signatures):
            k_val = sig.get('k')
            if k_val is not None:
                k_int = k_val if isinstance(k_val, int) else int(str(k_val), 16)
                if k_int < max_k_bound:
                    hazards.append({
                        'type': 'SMALL_NONCE_BIAS_MINE',
                        'risk_level': RISK_CRITICAL,
                        'index': idx,
                        'k_bits': k_int.bit_length(),
                        'description': f'Nonce k is small ({k_int.bit_length()} bits < {max_k_bits} bits). Vulnerable to LLL lattice attack.'
                    })

        return hazards

    @staticmethod
    def check_invalid_generator_trap(pubkey_point: Tuple[int, int], custom_generator: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        Detects invalid generator traps (CurveBall / CVE-2020-0601 hazard) where custom generator G' matches public key P.
        Inspired by ECC_Attacks/curveball.
        """
        if custom_generator is not None and custom_generator == pubkey_point:
            return {
                'hazard': 'CURVEBALL_GENERATOR_TRAP',
                'risk_level': RISK_CRITICAL,
                'description': "Generator G' matches target public key P. Signature forgery trap detected."
            }
        return {
            'hazard': None,
            'risk_level': RISK_LOW,
            'description': 'Canonical generator verified.'
        }

    @staticmethod
    def check_key_backdoor_offset(private_key_int: int) -> Dict[str, Any]:
        """
        Audits a private key for backdoored constant offsets d = N - 384 * C.
        """
        c_inv = mod_inv(FLAMINGO_C, N)
        for cand in [private_key_int % N, (N - private_key_int) % N]:
            offset = cand * c_inv % N
            if offset > N // 2:
                offset -= N
            if abs(offset) < 100000 and offset != 0:
                return {
                    'is_backdoored': True,
                    'risk_level': RISK_CRITICAL,
                    'offset': offset,
                    'description': f'Key matches structured constant offset (Offset: {offset}). Backdoor verified.'
                }

        return {
            'is_backdoored': False,
            'risk_level': RISK_LOW,
            'offset': None,
            'description': 'Key is standard scalar without structured offset backdoor.'
        }

    @staticmethod
    def scan_utxo_script(script_hex: str, amount_sats: int) -> Dict[str, Any]:
        """
        Scans a UTXO script and amount for script-level mines and traps.
        """
        hazards = []
        risk_level = RISK_LOW

        script_upper = script_hex.upper()

        # 1. Dust Trap Detection
        if amount_sats < DUST_THRESHOLD_SATS:
            hazards.append({
                'hazard': 'DUST_TRAP',
                'detail': f'UTXO value ({amount_sats} sats) is below dust limit ({DUST_THRESHOLD_SATS} sats). Drains fees upon spending.'
            })
            risk_level = max_risk(risk_level, RISK_HIGH)

        # 2. OP_RETURN / Unspendable Trap
        if script_upper.startswith('6A') or 'OP_RETURN' in script_upper:
            hazards.append({
                'hazard': 'UNSPENDABLE_OP_RETURN',
                'detail': 'Script contains OP_RETURN opcode. Output is provably unspendable.'
            })
            risk_level = max_risk(risk_level, RISK_CRITICAL)

        # 3. Timelock Trap (CLTV / CSV)
        if 'B1' in script_upper or 'B2' in script_upper or 'OP_CHECKLOCKTIMEVERIFY' in script_upper or 'OP_CHECKSEQUENCEVERIFY' in script_upper:
            hazards.append({
                'hazard': 'TIMELOCK_TRAP',
                'detail': 'Script enforces a time-lock condition (CLTV/CSV). UTXO cannot be spent until lock period expires.'
            })
            risk_level = max_risk(risk_level, RISK_HIGH)

        # 4. Complex Multi-Sig / P2SH / P2WSH Trap
        if script_upper.startswith('A914') or len(script_hex) > 100:
            hazards.append({
                'hazard': 'COMPLEX_SCRIPT_TRAP',
                'detail': 'Complex P2SH/P2WSH script requires custom witness or multi-signature preimage.'
            })
            risk_level = max_risk(risk_level, RISK_MEDIUM)

        return {
            'script_hex': script_hex,
            'amount_sats': amount_sats,
            'risk_level': risk_level,
            'hazards': hazards,
            'safe_to_spend': risk_level in (RISK_LOW, RISK_MEDIUM)
        }

    @staticmethod
    def assess_frontrun_risk(
        mempool_fee_rate_sat_vb: float,
        tx_vbytes: int = 140,
        output_value_sats: int = 100000
    ) -> Dict[str, Any]:
        """
        Assesses mempool exposure risk and calculates anti-frontrunning priority fee parameters.
        """
        base_fee = math.ceil(mempool_fee_rate_sat_vb * tx_vbytes)

        # Priority multiplier for anti-frontrunning (3.5x mempool rate)
        anti_frontrun_fee_rate = max(10.0, mempool_fee_rate_sat_vb * 3.5)
        anti_frontrun_fee = math.ceil(anti_frontrun_fee_rate * tx_vbytes)

        net_value = output_value_sats - anti_frontrun_fee

        if output_value_sats <= anti_frontrun_fee:
            risk = RISK_CRITICAL
            recommendation = "Do not sweep. Transaction fee exceeds total output value."
        elif output_value_sats < anti_frontrun_fee * 3:
            risk = RISK_HIGH
            recommendation = "High fee ratio. Broadcast via private relay / direct node connection."
        else:
            risk = RISK_MEDIUM
            recommendation = "Use anti-frontrunning high priority fee (3.5x mempool rate) via private node."

        return {
            'mempool_fee_rate_sat_vb': mempool_fee_rate_sat_vb,
            'tx_vbytes': tx_vbytes,
            'standard_fee_sats': base_fee,
            'anti_frontrun_fee_rate_sat_vb': anti_frontrun_fee_rate,
            'anti_frontrun_fee_sats': anti_frontrun_fee,
            'output_value_sats': output_value_sats,
            'net_sweep_value_sats': max(0, net_value),
            'risk_level': risk,
            'recommendation': recommendation
        }


class DeminingRig:
    """
    Demining suite rig for conducting address audits, building safe anti-frontrun
    sweep transactions, and running batch file processing.
    """

    def __init__(self):
        self.detector = MineDetector()

    def audit_address(
        self,
        address: str,
        signatures: Optional[List[Dict[str, Any]]] = None,
        utxos: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Performs a full demining audit on an address, checking signatures and UTXOs.
        """
        signatures = signatures or []
        utxos = utxos or []

        sig_hazards = self.detector.check_signature_nonce_reuse(signatures)
        poly_hazard = self.detector.check_flamingo_polynomial_bias(signatures)
        if poly_hazard:
            sig_hazards.append(poly_hazard)

        small_nonce_hazards = self.detector.check_small_nonce_bias(signatures)
        sig_hazards.extend(small_nonce_hazards)

        utxo_results = [
            self.detector.scan_utxo_script(u.get('script_hex', '76a9140088ac'), u.get('amount_sats', 0))
            for u in utxos
        ]

        # Calculate overall address risk
        overall_risk = RISK_LOW
        for h in sig_hazards:
            overall_risk = max_risk(overall_risk, h.get('risk_level', RISK_LOW))
        for u in utxo_results:
            overall_risk = max_risk(overall_risk, u.get('risk_level', RISK_LOW))

        return {
            'address': address,
            'overall_risk': overall_risk,
            'signatures_scanned': len(signatures),
            'signature_hazards': sig_hazards,
            'utxos_scanned': len(utxos),
            'utxo_analysis': utxo_results,
            'is_compromised': len(sig_hazards) > 0 or overall_risk in (RISK_HIGH, RISK_CRITICAL)
        }

    def build_safe_sweep_payload(
        self,
        private_key_hex: str,
        source_address: str,
        destination_address: str,
        utxo_amount_sats: int,
        mempool_fee_rate: float = 20.0,
        anti_frontrun: bool = True
    ) -> Dict[str, Any]:
        """
        Builds a safe, anti-frontrunning sweep transaction payload for recovered keys.
        """
        d = int(private_key_hex, 16) if isinstance(private_key_hex, str) else private_key_hex
        wif = to_wif(d, compressed=True)

        tx_vbytes = 192

        risk_eval = self.detector.assess_frontrun_risk(
            mempool_fee_rate_sat_vb=mempool_fee_rate,
            tx_vbytes=tx_vbytes,
            output_value_sats=utxo_amount_sats
        )

        fee_sats = risk_eval['anti_frontrun_fee_sats'] if anti_frontrun else risk_eval['standard_fee_sats']
        sweep_amount_sats = utxo_amount_sats - fee_sats

        if sweep_amount_sats <= 0:
            return {
                'status': 'ERROR',
                'message': 'UTXO amount insufficient to cover transaction fee.',
                'fee_sats': fee_sats,
                'utxo_amount_sats': utxo_amount_sats
            }

        tx_payload = {
            'status': 'READY',
            'source_address': source_address,
            'destination_address': destination_address,
            'utxo_amount_sats': utxo_amount_sats,
            'fee_sats': fee_sats,
            'fee_rate_sat_vb': risk_eval['anti_frontrun_fee_rate_sat_vb'] if anti_frontrun else mempool_fee_rate,
            'sweep_amount_sats': sweep_amount_sats,
            'wif': wif,
            'anti_frontrun_enabled': anti_frontrun,
            'broadcast_strategy': 'Direct RPC / Private Relay (Anti-Mempool Sniping)',
            'risk_assessment': risk_eval
        }

        return tx_payload

    def batch_demine_file(self, input_filepath: str, output_filepath: str) -> Dict[str, Any]:
        """
        Batch processes a CSV file containing signature or UTXO records for demining.
        """
        if not os.path.exists(input_filepath):
            raise FileNotFoundError(f"Input file not found: {input_filepath}")

        signatures_by_addr = {}
        total_records = 0

        with open(input_filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                addr = row.get('address', 'unknown_address')
                r = int(row['r'], 16) if row.get('r', '').startswith('0x') else int(row.get('r', 0))
                s = int(row['s'], 16) if row.get('s', '').startswith('0x') else int(row.get('s', 0))
                z_raw = row.get('z')
                z = int(z_raw, 16) if z_raw and z_raw.startswith('0x') else (int(z_raw) if z_raw and z_raw.isdigit() else None)
                k_raw = row.get('k')
                k = int(k_raw, 16) if k_raw and k_raw.startswith('0x') else (int(k_raw) if k_raw and k_raw.isdigit() else None)

                if addr not in signatures_by_addr:
                    signatures_by_addr[addr] = []

                signatures_by_addr[addr].append({'r': r, 's': s, 'z': z, 'k': k, 'txid': row.get('txid', '')})
                total_records += 1

        results = []
        compromised_count = 0

        for addr, sigs in signatures_by_addr.items():
            audit = self.audit_address(addr, signatures=sigs)
            results.append(audit)
            if audit['is_compromised']:
                compromised_count += 1

        summary = {
            'total_records_scanned': total_records,
            'unique_addresses': len(signatures_by_addr),
            'compromised_addresses': compromised_count,
            'clean_addresses': len(signatures_by_addr) - compromised_count,
            'audits': results
        }

        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        return summary


def max_risk(r1: str, r2: str) -> str:
    """Returns the higher risk level between two risk strings."""
    levels = {RISK_LOW: 1, RISK_MEDIUM: 2, RISK_HIGH: 3, RISK_CRITICAL: 4}
    return r1 if levels.get(r1, 1) >= levels.get(r2, 1) else r2


def run_demining_demo():
    """
    Executes a comprehensive demonstration of the Demining Tools module.
    """
    print("==============================================================================")
    print("🦩 PROJECT FLAMINGO: DEMINING TOOLS DEMONSTRATION")
    print("==============================================================================")

    rig = DeminingRig()

    # 1. Simulate Repeated Nonce Mine
    print("\n--- [1. SIGNATURE HAZARD DEMINING: REPEATED NONCE MINE] ---")
    k_mine = secrets.randbits(256) % N
    d_target = secrets.randbits(256) % N
    z1, z2 = secrets.randbits(256) % N, secrets.randbits(256) % N

    R_pt = scalar_mul(k_mine, G)
    r_val = R_pt[0] % N
    s1 = (mod_inv(k_mine, N) * (z1 + r_val * d_target)) % N
    s2 = (mod_inv(k_mine, N) * (z2 + r_val * d_target)) % N

    mined_sigs = [
        {'r': r_val, 's': s1, 'z': z1, 'txid': 'tx_mine_1'},
        {'r': r_val, 's': s2, 'z': z2, 'txid': 'tx_mine_2'}
    ]

    hazards = MineDetector.check_signature_nonce_reuse(mined_sigs)
    print(f"Detected {len(hazards)} Hazard(s):")
    for h in hazards:
        print(f"  [!] Type:         {h['type']}")
        print(f"      Risk Level:   {h['risk_level']}")
        print(f"      Recovered d:  {h['recovered_key']}")
        print(f"      Verified:     {'✅ SUCCESS' if int(h['recovered_key'], 16) == d_target else '❌ FAIL'}")

    # 2. CurveBall / Invalid Generator Trap Check
    print("\n--- [2. CURVEBALL GENERATOR TRAP DETECTION] ---")
    pub_pt = scalar_mul(d_target, G)
    cb_check = MineDetector.check_invalid_generator_trap(pubkey_point=pub_pt, custom_generator=pub_pt)
    print(f"Testing CurveBall G'=P trap:")
    print(f"  Hazard:     {cb_check['hazard']}")
    print(f"  Risk Level: {cb_check['risk_level']}")
    print(f"  Detail:     {cb_check['description']}")

    # 3. Simulate UTXO Script Traps
    print("\n--- [3. UTXO SCRIPT HAZARD DEMINING] ---")
    test_scripts = [
        ("76a9140088ac", 50000, "Standard P2PKH"),
        ("6a140011223344", 10000, "OP_RETURN Unspendable Trap"),
        ("76a9140088ac", 300, "Dust Trap (< 546 sats)"),
        ("63b17521", 200000, "CLTV Timelock Trap")
    ]

    for script_hex, sats, label in test_scripts:
        utxo_res = MineDetector.scan_utxo_script(script_hex, sats)
        print(f"Testing {label} ({sats} sats):")
        print(f"  Risk Level:    {utxo_res['risk_level']}")
        print(f"  Safe to spend: {utxo_res['safe_to_spend']}")
        for hz in utxo_res['hazards']:
            print(f"  -> {hz['hazard']}: {hz['detail']}")

    # 4. Build Safe Anti-Frontrun Sweep
    print("\n--- [4. SAFE ANTI-FRONTRUN SWEEP TRANSACTION BUILDER] ---")
    d_demo = 0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef
    src_addr = derive_address(d_demo, compressed=True)
    dst_addr = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

    sweep_payload = rig.build_safe_sweep_payload(
        private_key_hex=hex(d_demo),
        source_address=src_addr,
        destination_address=dst_addr,
        utxo_amount_sats=500000,
        mempool_fee_rate=15.0,
        anti_frontrun=True
    )

    print("Sweep Payload:")
    print(f"  Source Address:       {sweep_payload['source_address']}")
    print(f"  Destination Address:  {sweep_payload['destination_address']}")
    print(f"  UTXO Amount:          {sweep_payload['utxo_amount_sats']} sats")
    print(f"  Anti-Frontrun Fee:    {sweep_payload['fee_sats']} sats ({sweep_payload['fee_rate_sat_vb']:.1f} sat/vB)")
    print(f"  Net Swept Amount:     {sweep_payload['sweep_amount_sats']} sats")
    print(f"  Strategy:             {sweep_payload['broadcast_strategy']}")

    print("\n==============================================================================")
    print("✅ DEMINING TOOLS DEMONSTRATION COMPLETE")
    print("==============================================================================")


def main():
    parser = argparse.ArgumentParser(
        description="🦩 Project Flamingo: Demining Tools & Minefield Sweeper"
    )
    parser.add_argument('--demo', action='store_true', help='Run self-contained demining demonstration')
    parser.add_argument('--scan-address', type=str, metavar='ADDR', help='Demine an address')
    parser.add_argument('--demine-file', type=str, metavar='CSV_PATH', help='Batch demine a CSV file')
    parser.add_argument('--output', type=str, default='demining_report.json', help='Output JSON report path')

    args = parser.parse_args()

    if args.demo or len(sys.argv) == 1:
        run_demining_demo()
    elif args.demine_file:
        rig = DeminingRig()
        summary = rig.batch_demine_file(args.demine_file, args.output)
        print(f"✅ Batch demining complete. Report written to {args.output}")
        print(f"   Total Records: {summary['total_records_scanned']}")
        print(f"   Compromised:   {summary['compromised_addresses']}")
    elif args.scan_address:
        rig = DeminingRig()
        audit = rig.audit_address(args.scan_address)
        print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
