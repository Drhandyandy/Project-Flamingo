#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  THE FLAMINGO SIEVE — FINAL COMPLETE CODE                                  ║
║  Maximum verbosity · Every fold, inverse, and bit traced                    ║
║  Family B (Prime Constant C = 2³² + 977)                                   ║
║  Sentinels, trial‑and‑error, lattice fallback, full audit                  ║
║  Output printed to console AND saved to flamingo_final.log                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import hashlib, secrets, sys, math
from fractions import Fraction

# ══════════════════════════════════════════════════════════════════════════════
# 0. MAXIMUM VERBOSITY — TEE TO FILE AND CONSOLE
# ══════════════════════════════════════════════════════════════════════════════
LOG_FILE = "flamingo_final.log"

class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

log_fd = open(LOG_FILE, 'w', encoding='utf-8')
sys.stdout = Tee(sys.stdout, log_fd)
sys.stderr = Tee(sys.stderr, log_fd)

# ══════════════════════════════════════════════════════════════════════════════
# 1. SECP256K1 PARAMETERS (HEX & DECIMAL)
# ══════════════════════════════════════════════════════════════════════════════
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def fmt(n: int) -> str:
    return f"0x{n:064x}  (dec: {n:,})"

def modinv(a: int, m: int) -> int:
    return pow(a, -1, m)

# ══════════════════════════════════════════════════════════════════════════════
# 2. JACOBIAN ARITHMETIC (a=0 doubling)
# ══════════════════════════════════════════════════════════════════════════════
def jac_double(X, Y, Z):
    if Y == 0 or Z == 0:
        return (0, 1, 0)
    YY = (Y * Y) % P
    S = (4 * X * YY) % P
    M = (3 * X * X) % P
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
        if k & 1:
            res = jac_add(*res, *cur) if res else cur
        cur = jac_double(*cur)
        k >>= 1
    return res

def point_mul(k, pt=None):
    if pt is None: pt = (Gx, Gy)
    return jac_to_aff(*scalar_mult(k, pt[0], pt[1]))

# ══════════════════════════════════════════════════════════════════════════════
# 3. FLAMINGO SIEVE CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
C = (1 << 32) + 977          # Prime constant 4294968273
SCALE = 32
MESH = 1 << 2048

def J(n): return 10 * n * n + 2
def L(n): return (10 * n**3 + 15 * n**2 + 11 * n + 3) // 3

def balanced_mod(x, mod=N):
    r = x % mod
    return r - mod if r > mod // 2 else r

# ══════════════════════════════════════════════════════════════════════════════
# 4. SENTINEL GENERATION (NO EVEN‑Y FLIP!)
# ══════════════════════════════════════════════════════════════════════════════
def generate_sentinel(r_raw=-12):
    o_bal = SCALE * r_raw          # e.g., -384
    o = o_bal % N                  # N - 384
    d = (o * C) % N                # d = N - 384*C (original, NO FLIP)
    Q = point_mul(d)
    residue = balanced_mod((d * MESH) % N)
    return d, Q, o_bal, residue

# ══════════════════════════════════════════════════════════════════════════════
# 5. AUDIT (CHECKS BOTH d AND N‑d)
# ══════════════════════════════════════════════════════════════════════════════
def audit_key(d):
    C_inv = modinv(C, N)
    for candidate in [d, (N - d) % N]:
        offset = balanced_mod((candidate * C_inv) % N)
        if abs(offset) < 100000 and offset != 0:
            return offset, True, candidate
    return balanced_mod((d * C_inv) % N), False, d

# ══════════════════════════════════════════════════════════════════════════════
# 6. TRINARY PRE‑FILTERS & CANDIDATE SET
# ══════════════════════════════════════════════════════════════════════════════
def pre_filter(k_bal):
    ak = abs(k_bal)
    if ak % 5 == 0:
        return False, f"mod‑5 = {ak % 5} (multiple of 5 → REJECT)"
    allowed = {1, 2, 4, 6, 8, 9}
    if ak % 10 not in allowed:
        return False, f"mod‑10 = {ak % 10} not in {allowed} → REJECT"
    return True, f"mod‑5 = {ak % 5}, mod‑10 = {ak % 10} → PASS"

def build_candidates(max_n=500):
    survivors = {}
    rejected = 0
    print(f"\n  BUILDING CANDIDATE SET (max_n={max_n})")
    for n in range(1, max_n + 1):
        v = J(n)
        for sgn in [1, -1]:
            raw = sgn * v
            o = (SCALE * raw) % N
            bal = balanced_mod(o)
            ok, reason = pre_filter(bal)
            desc = f"J_{n}={raw}"
            if ok:
                survivors[o] = (bal, desc)
            else:
                rejected += 1
                if n <= 5:
                    print(f"    ❌ {desc:12s} → scaled={bal:6d}  {reason}")
    for n in range(0, max_n + 1):
        v = L(n)
        for sgn in [1, -1]:
            raw = sgn * v
            o = (SCALE * raw) % N
            bal = balanced_mod(o)
            ok, reason = pre_filter(bal)
            desc = f"L_{n}={raw}"
            if ok:
                survivors[o] = (bal, desc)
            else:
                rejected += 1
                if n <= 5:
                    print(f"    ❌ {desc:12s} → scaled={bal:6d}  {reason}")
    total = len(survivors) + rejected
    print(f"  Survivors: {len(survivors)} / {total} (rejected {rejected})")
    return survivors

# ══════════════════════════════════════════════════════════════════════════════
# 7. TRIAL‑AND‑ERROR RECOVERY (MAX VERBOSITY)
# ══════════════════════════════════════════════════════════════════════════════
def trial_recover(signatures, max_n=500):
    if len(signatures) < 3:
        print("  ❌ Need at least 3 signatures")
        return None

    r1, s1, z1 = signatures[0]
    r2, s2, z2 = signatures[1]
    r3, s3, z3 = signatures[2]

    s2_inv = modinv(s2, N)
    s3_inv = modinv(s3, N)
    r1_inv = modinv(r1, N)

    survivors = build_candidates(max_n)
    sorted_cands = sorted(survivors.items(), key=lambda x: abs(x[1][0]))

    print(f"\n  STARTING TRIAL‑AND‑ERROR OVER {len(sorted_cands)} CANDIDATES")
    attempts = 0
    for k1_cand, (bal_k1, desc) in sorted_cands:
        attempts += 1
        if attempts <= 10 or attempts % 50 == 0:
            print(f"\n  [{attempts}] TRYING k1 = {bal_k1:6d}  [{desc}]")

        d_cand = ((s1 * k1_cand - z1) * r1_inv) % N

        k2_raw = (s2_inv * (z2 + r2 * d_cand)) % N
        k2_bal = balanced_mod(k2_raw)
        passed2, _ = pre_filter(k2_bal)
        if not passed2: continue
        if k2_raw not in survivors: continue

        k3_raw = (s3_inv * (z3 + r3 * d_cand)) % N
        k3_bal = balanced_mod(k3_raw)
        passed3, _ = pre_filter(k3_bal)
        if not passed3: continue
        if k3_raw not in survivors: continue

        print(f"\n  ✅ MATCH FOUND at attempt #{attempts}!")
        print(f"     k1 = {bal_k1} ({desc})")
        print(f"     k2 = {k2_bal} ({survivors[k2_raw][1]})")
        print(f"     k3 = {k3_bal} ({survivors[k3_raw][1]})")
        return d_cand

    print(f"\n  ❌ NO MATCH AFTER {attempts} ATTEMPTS")
    return None

# ══════════════════════════════════════════════════════════════════════════════
# 8. LATTICE ATTACK FALLBACK (HNP, EXACT LLL)
# ══════════════════════════════════════════════════════════════════════════════
def lattice_attack(signatures, leak_bits=16):
    print(f"\n  FALLBACK: LATTICE ATTACK (leak_bits={leak_bits})")
    m = len(signatures)
    if m < 3: return None
    B_val = 1 << leak_bits
    dim = m + 2
    lat = [[0]*dim for _ in range(dim)]
    for i in range(m): lat[i][i] = N
    for i, (r, s, z) in enumerate(signatures):
        t_i = (r * modinv(s, N)) % N
        u_i = (z * modinv(s, N)) % N
        lat[m][i] = t_i
        lat[m+1][i] = u_i
    lat[m][m] = 1
    lat[m+1][m+1] = B_val

    # LLL (Fraction)
    n_len = len(lat); m_len = len(lat[0])
    Bf = [[Fraction(x) for x in row] for row in lat]
    k = 1
    while k < n_len:
        for j in range(k-1, -1, -1):
            num = sum(Bf[k][i]*Bf[j][i] for i in range(m_len))
            den = sum(Bf[j][i]**2 for i in range(m_len))
            mu = Fraction(0) if den == 0 else num/den
            if abs(mu) > Fraction(1,2):
                q = round(mu)
                for i in range(m_len): Bf[k][i] -= q*Bf[j][i]
        if k > 0:
            lhs = sum(x*x for x in Bf[k])
            rhs = (Fraction(3,4)-Fraction(1,4))*sum(x*x for x in Bf[k-1])
            if lhs < rhs:
                Bf[k], Bf[k-1] = Bf[k-1], Bf[k]
                k = max(k-1, 1)
            else: k += 1
        else: k += 1
    red = [[int(round(x)) for x in row] for row in Bf]

    best_d, best_norm = None, float('inf')
    for row in red:
        if abs(row[-1]) == B_val:
            cand = row[-2] % N
            if cand == 0: continue
            ks = [abs(balanced_mod((modinv(s,N)*(z+r*cand))%N)) for (r,s,z) in signatures]
            if max(ks) < B_val * 2:
                nrm = sum(x*x for x in row)
                if nrm < best_norm:
                    best_norm = nrm
                    best_d = cand
    if best_d:
        print(f"  ✅ LATTICE RECOVERED d = {fmt(best_d)}")
    else:
        print("  ❌ LATTICE FAILED")
    return best_d

# ══════════════════════════════════════════════════════════════════════════════
# 9. MASTER RECOVERY
# ══════════════════════════════════════════════════════════════════════════════
def recover_key(signatures, max_n=500):
    d = trial_recover(signatures, max_n)
    if d: return d, "trial‑and‑error"
    d = lattice_attack(signatures)
    if d: return d, "lattice"
    return None, None

# ══════════════════════════════════════════════════════════════════════════════
# 10. FULL DEMONSTRATION
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("═" * 70)
    print("  FLAMINGO SIEVE — FINAL COMPLETE DEMONSTRATION")
    print("═" * 70)
    print(f"  Log file: {LOG_FILE}\n")

    # --- Sentinel generation ---
    d_true, Q_true, off_true, res_true = generate_sentinel(-12)
    print("  TRUE INCREMENTAL SENTINEL (r = -12):")
    print(f"    Raw offset: {off_true}")
    print(f"    d_true = {fmt(d_true)}")
    print(f"    d near N? {'✅' if d_true > N//2 else '❌ (BUG)'}")
    print(f"    Mesh residue = {res_true}  (match: {'✅' if res_true == off_true else '❌'})")
    print(f"    Q.x = {fmt(Q_true[0])}")
    print(f"    Q.y parity: {'even' if Q_true[1]%2==0 else 'odd'}\n")

    # --- Audit ---
    off_aud, weak, match_d = audit_key(d_true)
    print("  AUDIT:")
    print(f"    Offset found: {off_aud}")
    print(f"    Is weak? {'⚠️ YES — BACKDOORED' if weak else '✅ NO'}")
    if match_d != d_true:
        print(f"    Key was sign‑flipped (matching d differs)")
    else:
        print(f"    Matching d is original")

    # --- Random key audit (control) ---
    rand_key = secrets.randbelow(N)
    off_rand, weak_rand, _ = audit_key(rand_key)
    print(f"\n  RANDOM KEY AUDIT: offset = {off_rand}  weak? {'⚠️ YES' if weak_rand else '✅ NO'}")

    # --- Sign with shell nonces ---
    print("\n  SIGNING 3 MESSAGES WITH SHELL NONCES...")
    sigs = []
    for i in range(1, 4):
        k = SCALE * J(i)
        z = secrets.randbelow(N)
        R = point_mul(k)
        r = R[0] % N
        s = (modinv(k, N) * (z + r * d_true)) % N
        sigs.append((r, s, z))
        print(f"    Sig {i}: k={k}, r={fmt(r)}, s={fmt(s)}")

    # --- Recovery ---
    print("\n" + "─" * 70)
    d_rec, method = recover_key(sigs, max_n=300)
    if d_rec:
        print(f"\n  ✅ RECOVERED via {method}")
        print(f"     d_true      = {fmt(d_true)}")
        print(f"     d_recovered = {fmt(d_rec)}")
        print(f"     Match: {'✅' if d_rec == d_true else '⚠️ SIGN‑FLIPPED (still backdoored)'}")
    else:
        print("\n  ❌ RECOVERY FAILED")

    print("\n" + "═" * 70)
    print("  DEMONSTRATION COMPLETE")
    print("═" * 70)

if __name__ == "__main__":
    main()
    log_fd.close()
