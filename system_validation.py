from crypto_utils import *
from apex_solver import ResonantKangarooAMOS
import hashlib

def run_system_validation():
    print("--- [PROJECT FLAMINGO: SYSTEM VALIDATION (SOVEREIGN)] ---")

    # 1. Cryptographic Primitives
    print("[1/4] Validating EC Primitives...")
    assert mod_inv(3, 11) == 4
    p1 = scalar_mul(1, G)
    assert p1 == G

    # Jacobian
    j1 = to_jacobian(G)
    j2 = jacobian_double(j1)
    assert from_jacobian(j2) == ec_double(G)
    print("      Primitives: OK")

    # 2. Address Derivation
    print("[2/4] Validating Address Derivation...")
    # P1
    assert derive_address(1, mode='standard', compressed=True) == '1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH'
    # P71 Apex (Standard Mode Verification)
    assert derive_address(0x68a282e9b049edb508, mode='standard') == '1HSFck3ePBRaF81wBBDrMNggPstMWFvjUv'
    print("      Derivation: OK")

    # 3. RK-AMOS Engine
    print("[3/4] Validating RK-AMOS Solver...")
    target_d = 12345
    target_q = scalar_mul(target_d, G)
    # Search in small range for speed
    solver = ResonantKangarooAMOS(target_q, 10000, 20000, {'distinguished_bits': 2})
    res = solver.solve()
    assert res == 12345
    print("      RK-AMOS: OK")

    # 4. Manifest Integrity
    print("[4/4] Validating Manifest Alignment...")
    # Pulse 656
    p = get_pulse_656()
    assert p == pow(2, 656, N)
    print("      Manifest: OK")

    print("\n✅ SYSTEM STATUS: SOVEREIGN")

if __name__ == "__main__":
    run_system_validation()
