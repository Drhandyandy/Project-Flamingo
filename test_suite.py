"""
PROJECT FLAMINGO: COMPREHENSIVE TEST SUITE
Tests all cryptographic primitives and solver functionality
"""

import sys
from crypto_utils import *
from apex_solver import KangarooSolver

def test_modular_inverse():
    """Test Extended Euclidean Algorithm for modular inverse"""
    print("[TEST 1] Modular Inverse")
    
    # Test case 1: Simple example
    assert mod_inv(3, 11) == 4, "mod_inv(3, 11) should be 4"
    assert (3 * 4) % 11 == 1, "Verification: 3*4 mod 11 = 1"
    
    # Test case 2: Modular inverse in secp256k1 field
    a = 123456789
    a_inv = mod_inv(a, P)
    assert (a * a_inv) % P == 1, f"a * a_inv mod P should equal 1"
    
    print("   ✅ PASS: Modular inverse correct")

def test_affine_operations():
    """Test affine point addition and doubling"""
    print("[TEST 2] Affine EC Operations")
    
    # Test case 1: Point doubling
    g_double = ec_double(G)
    g_double_affine = ec_add(G, G)
    assert g_double == g_double_affine, "ec_double(G) should equal ec_add(G, G)"
    
    # Test case 2: Point addition with self
    p = scalar_mul(5, G)
    p_plus_p = ec_add(p, p)
    p_double = ec_double(p)
    assert p_plus_p == p_double, "P + P should equal 2P"
    
    # Test case 3: Scalar multiplication verification
    d = 12345
    q = scalar_mul(d, G)
    assert q is not None, "Scalar multiplication should not return None"
    assert isinstance(q, tuple), "Result should be a point tuple"
    
    print("   ✅ PASS: Affine operations correct")

def test_jacobian_coordinates():
    """Test Jacobian coordinate conversions and operations"""
    print("[TEST 3] Jacobian Coordinates")
    
    # Test case 1: Affine ↔ Jacobian conversion
    j_g = to_jacobian(G)
    g_recovered = from_jacobian(j_g)
    assert g_recovered == G, "Affine ↔ Jacobian conversion should be lossless"
    
    # Test case 2: Jacobian doubling matches affine
    j_double = jacobian_double(j_g)
    j_recovered = from_jacobian(j_double)
    affine_double = ec_double(G)
    assert j_recovered == affine_double, "Jacobian double should match affine double"
    
    # Test case 3: Jacobian addition matches affine
    p = scalar_mul(7, G)
    q = scalar_mul(11, G)
    
    j_p = to_jacobian(p)
    j_q = to_jacobian(q)
    j_sum = jacobian_add(j_p, j_q)
    j_sum_affine = from_jacobian(j_sum)
    
    affine_sum = ec_add(p, q)
    assert j_sum_affine == affine_sum, "Jacobian addition should match affine addition"
    
    print("   ✅ PASS: Jacobian coordinates correct")

def test_scalar_multiplication():
    """Test scalar multiplication via double-and-add"""
    print("[TEST 4] Scalar Multiplication")
    
    # Test case 1: Scalar 1
    q1 = scalar_mul(1, G)
    assert q1 == G, "1 * G should equal G"
    
    # Test case 2: Scalar 2
    q2 = scalar_mul(2, G)
    assert q2 == ec_double(G), "2 * G should equal 2P"
    
    # Test case 3: Distributive property
    a, b = 123, 456
    qa = scalar_mul(a, G)
    qb = scalar_mul(b, G)
    q_sum_direct = scalar_mul(a + b, G)
    q_sum_computed = ec_add(qa, qb)
    assert q_sum_direct == q_sum_computed, "(a+b)*G should equal a*G + b*G"
    
    # Test case 4: Large scalar
    large = 2**200
    q_large = scalar_mul(large, G)
    assert q_large is not None, "Scalar multiplication should handle large values"
    
    print("   ✅ PASS: Scalar multiplication correct")

def test_bitcoin_address_derivation():
    """Test Bitcoin P2PKH address derivation pipeline"""
    print("[TEST 5] Bitcoin Address Derivation")
    
    # Test case 1: Known address for scalar 1
    addr_1 = derive_address(1, mode='standard', compressed=True)
    expected_1 = '1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH'
    assert addr_1 == expected_1, f"Address for scalar 1 should be {expected_1}, got {addr_1}"
    
    # Test case 2: Address determinism
    addr_2a = derive_address(999, mode='standard', compressed=True)
    addr_2b = derive_address(999, mode='standard', compressed=True)
    assert addr_2a == addr_2b, "Address derivation should be deterministic"
    
    # Test case 3: Compressed vs uncompressed
    addr_comp = derive_address(42, mode='standard', compressed=True)
    addr_uncomp = derive_address(42, mode='standard', compressed=False)
    assert addr_comp != addr_uncomp, "Compressed and uncompressed should differ"
    assert len(addr_comp) <= len(addr_uncomp), "Compressed should be ≤ uncompressed length"
    
    print("   ✅ PASS: Bitcoin address derivation correct")

def test_wif_encoding():
    """Test Wallet Import Format encoding"""
    print("[TEST 6] WIF Encoding")
    
    # Test case 1: WIF generation
    private_key = 12345
    wif = to_wif(private_key, compressed=True)
    assert isinstance(wif, str), "WIF should be a string"
    assert wif.startswith('K') or wif.startswith('L'), "Compressed WIF should start with K or L"
    
    # Test case 2: WIF uncompressed
    wif_uncomp = to_wif(private_key, compressed=False)
    assert wif_uncomp.startswith('5'), "Uncompressed WIF should start with 5"
    
    print("   ✅ PASS: WIF encoding correct")

def test_kangaroo_solver_small():
    """Test KangarooSolver on small range (known recovery)"""
    print("[TEST 7] Kangaroo Solver (Small Range)")
    
    # Small test: private key 514 in range [512, 1023]
    target_d = 514
    target_q = scalar_mul(target_d, G)
    
    solver = KangarooSolver(
        target_q,
        min_range=512,
        max_range=1023,
        options={
            'max_iterations': 100000,
            'distinguished_bits': 8
        }
    )
    
    result = solver.solve()
    assert result is not None, "Solver should find a result"
    assert result == target_d, f"Solver should recover {target_d}, got {result}"
    
    print("   ✅ PASS: Kangaroo solver converged correctly")

def test_kangaroo_solver_medium():
    """Test KangarooSolver on medium range"""
    print("[TEST 8] Kangaroo Solver (Medium Range)")
    
    # Medium test: private key 12345 in range [10000, 20000]
    target_d = 12345
    target_q = scalar_mul(target_d, G)
    
    solver = KangarooSolver(
        target_q,
        min_range=10000,
        max_range=20000,
        options={
            'max_iterations': 500000,
            'distinguished_bits': 12
        }
    )
    
    result = solver.solve()
    assert result is not None, "Solver should find a result"
    assert result == target_d, f"Solver should recover {target_d}, got {result}"
    
    print("   ✅ PASS: Kangaroo solver converged on medium range")

def test_pulse_656():
    """Test Pulse 656 calculation"""
    print("[TEST 9] Pulse 656 Manifold")
    
    pulse = get_pulse_656()
    expected = pow(2, 656, N)
    assert pulse == expected, "Pulse 656 calculation should be correct"
    assert isinstance(pulse, int), "Pulse should be an integer"
    
    print("   ✅ PASS: Pulse 656 manifold correct")

def test_sovereign_sequence():
    """Test OEIS A369920 sequence"""
    print("[TEST 10] Sovereign Sequence (OEIS A369920)")
    
    # Import sovereign sequence function
    from sovereign_sequence import a_n
    
    # Test case 1: Known values
    assert a_n(0) == 1, "a_n(0) should be 1"
    assert a_n(1) == 13, "a_n(1) should be 13"
    
    # Test case 2: Monotonicity
    for n in range(10):
        assert a_n(n) < a_n(n+1), f"Sequence should be monotonic: a_n({n}) < a_n({n+1})"
    
    print("   ✅ PASS: Sovereign sequence correct")

def run_all_tests():
    """Execute all tests and report results"""
    print("=" * 70)
    print("🦩 PROJECT FLAMINGO: COMPREHENSIVE TEST SUITE 🦩")
    print("=" * 70)
    print()
    
    tests = [
        test_modular_inverse,
        test_affine_operations,
        test_jacobian_coordinates,
        test_scalar_multiplication,
        test_bitcoin_address_derivation,
        test_wif_encoding,
        test_kangaroo_solver_small,
        test_kangaroo_solver_medium,
        test_pulse_656,
        test_sovereign_sequence,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ FAIL: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"   ❌ ERROR: {type(e).__name__}: {str(e)}")
            failed += 1
        print()
    
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
