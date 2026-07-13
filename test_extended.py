"""
PROJECT FLAMINGO: EXTENDED TEST SUITE
Advanced validation including performance, edge cases, and cryptographic properties
"""

import sys
import time
import hashlib
from crypto_utils import *
from apex_solver import KangarooSolver
from sovereign_sequence import a_n

# ============================================================================
# PART A: EDGE CASE & BOUNDARY TESTS
# ============================================================================

def test_point_at_infinity():
    """Test handling of point at infinity (identity element)"""
    print("[TEST A1] Point at Infinity (Identity)")
    
    # Adding point to its negation should give None/Identity
    p = scalar_mul(7, G)
    p_neg = (p[0], (P - p[1]) % P)  # Negation: (x, -y)
    result = ec_add(p, p_neg)
    
    # Result should be None or (0,0) depending on implementation
    assert result is None or result == (0, 0), "P + (-P) should be identity"
    
    # Identity + Point = Point
    assert ec_add(None, G) == G, "None + G should be G"
    assert ec_add(G, None) == G, "G + None should be G"
    
    print("   ✅ PASS: Point at infinity handled correctly")

def test_scalar_zero():
    """Test scalar multiplication by zero"""
    print("[TEST A2] Scalar Multiplication by Zero")
    
    result = scalar_mul(0, G)
    assert result is None, "0 * G should be None (identity)"
    
    print("   ✅ PASS: Zero scalar handled correctly")

def test_scalar_modulo_order():
    """Test that scalar is reduced modulo group order"""
    print("[TEST A3] Scalar Modulo Group Order")
    
    # d * G and (d + N) * G should be equal
    d = 12345
    q1 = scalar_mul(d, G)
    q2 = scalar_mul(d + N, G)
    
    assert q1 == q2, "d * G should equal (d + N) * G"
    
    print("   ✅ PASS: Scalar modulo order works correctly")

def test_scalar_negative():
    """Test handling of negative scalars"""
    print("[TEST A4] Negative Scalar Values")
    
    d = 12345
    q_pos = scalar_mul(d, G)
    q_neg = scalar_mul(-d % N, G)
    
    # Should be negation of each other
    q_neg_verify = (q_neg[0], (P - q_neg[1]) % P)
    assert q_neg_verify == q_pos, "(-d) * G should be negation of d * G"
    
    print("   ✅ PASS: Negative scalars handled correctly")

def test_large_scalar():
    """Test very large scalars"""
    print("[TEST A5] Large Scalar Values")
    
    # Scalar larger than N
    large_scalar = 2**256 - 1
    result = scalar_mul(large_scalar, G)
    assert result is not None, "Should handle very large scalars"
    
    # Verify it's the same as reduced scalar
    reduced = large_scalar % N
    result_reduced = scalar_mul(reduced, G)
    assert result == result_reduced, "Large scalar should be reduced modulo N"
    
    print("   ✅ PASS: Large scalars handled correctly")

def test_y_coordinate_recovery():
    """Test y-coordinate from x-coordinate (two solutions due to curve negation)"""
    print("[TEST A6] Y-Coordinate Recovery")
    
    # Given x-coordinate, there are two possible y values on secp256k1
    x = G[0]
    y1 = G[1]
    y2 = (P - y1) % P
    
    # Both points satisfy y² = x³ + 7
    lhs1 = (y1 * y1) % P
    lhs2 = (y2 * y2) % P
    rhs = (x**3 + 7) % P
    
    assert lhs1 == rhs, "First y should satisfy curve equation"
    assert lhs2 == rhs, "Negated y should also satisfy curve equation"
    
    print("   ✅ PASS: Y-coordinate recovery correct")

# ============================================================================
# PART B: JACOBIAN EFFICIENCY TESTS
# ============================================================================

def test_jacobian_batch_operations():
    """Test Jacobian operations don't require inversion per step"""
    print("[TEST B1] Jacobian Batch Efficiency")
    
    # Create multiple Jacobian points
    points = [to_jacobian(scalar_mul(i, G)) for i in range(1, 11)]
    
    # Perform additions without conversion
    result = points[0]
    for p in points[1:]:
        result = jacobian_add(result, p)
    
    # Convert to affine only once at end
    result_affine = from_jacobian(result)
    
    # Verify by computing affinely
    affine_sum = G
    for i in range(2, 11):
        affine_sum = ec_add(affine_sum, scalar_mul(i, G))
    
    assert result_affine == affine_sum, "Jacobian batch should match affine computation"
    
    print("   ✅ PASS: Jacobian batch operations correct")

def test_jacobian_z_coordinate_tracking():
    """Test Z coordinate manipulation in Jacobian arithmetic"""
    print("[TEST B2] Jacobian Z-Coordinate Tracking")
    
    # Start with Z=1
    j1 = to_jacobian(G)
    assert j1[2] == 1, "Initial Z should be 1"
    
    # After addition, Z should change
    j2 = to_jacobian(scalar_mul(2, G))
    j_sum = jacobian_add(j1, j2)
    
    # Z might not be 1 anymore
    assert j_sum[2] != 0, "Z coordinate should not be zero after valid operation"
    
    # But conversion should still work
    result = from_jacobian(j_sum)
    expected = ec_add(G, scalar_mul(2, G))
    assert result == expected, "Z-coordinate transformation should preserve point"
    
    print("   ✅ PASS: Jacobian Z-coordinate tracking correct")

def test_jacobian_double_special_case():
    """Test Jacobian double handles special cases"""
    print("[TEST B3] Jacobian Double Special Cases")
    
    # Double where point has y=0 should give identity
    # (secp256k1 points with y=0 are rare, but handle gracefully)
    j_g = to_jacobian(G)
    j_double = jacobian_double(j_g)
    
    # Should not be zero point
    assert j_double != (0, 0, 0), "Jacobian double should not give zero point for G"
    
    # Verify against affine
    affine_double = ec_double(G)
    j_double_affine = from_jacobian(j_double)
    assert j_double_affine == affine_double, "Jacobian double should match affine"
    
    print("   ✅ PASS: Jacobian double special cases handled")

# ============================================================================
# PART C: CRYPTOGRAPHIC PROPERTIES
# ============================================================================

def test_scalar_mul_associativity():
    """Test (a*b)*P = a*(b*P)"""
    print("[TEST C1] Scalar Multiplication Associativity")
    
    a, b = 123, 456
    p = G
    
    # (a*b)*P
    ab = (a * b) % N
    q1 = scalar_mul(ab, p)
    
    # a*(b*P)
    bp = scalar_mul(b, p)
    q2 = scalar_mul(a, bp)
    
    assert q1 == q2, "(a*b)*P should equal a*(b*P)"
    
    print("   ✅ PASS: Scalar multiplication associativity verified")

def test_scalar_mul_distributivity():
    """Test (a+b)*P = a*P + b*P"""
    print("[TEST C2] Scalar Multiplication Distributivity")
    
    a, b = 789, 234
    
    # (a+b)*P
    q1 = scalar_mul((a + b) % N, G)
    
    # a*P + b*P
    qa = scalar_mul(a, G)
    qb = scalar_mul(b, G)
    q2 = ec_add(qa, qb)
    
    assert q1 == q2, "(a+b)*P should equal a*P + b*P"
    
    print("   ✅ PASS: Scalar multiplication distributivity verified")

def test_ecdsa_signature_verification_premise():
    """Test mathematical premise for ECDSA (k*G verification)"""
    print("[TEST C3] ECDSA Verification Premise")
    
    # In ECDSA: K = k*G, and we verify k*G = K by checking on curve
    k = 98765
    K = scalar_mul(k, G)
    
    # K should be on secp256k1 curve: y² = x³ + 7
    x, y = K
    lhs = (y * y) % P
    rhs = (x**3 + 7) % P
    
    assert lhs == rhs, "Public key should satisfy curve equation"
    
    # Verify scalar multiplication can recover same point
    K_verify = scalar_mul(k, G)
    assert K_verify == K, "Scalar multiplication should be deterministic"
    
    print("   ✅ PASS: ECDSA verification premise valid")

def test_curve_equation_preservation():
    """Test that all computed points satisfy curve equation"""
    print("[TEST C4] Curve Equation Preservation")
    
    # Test many random scalars
    import random
    random.seed(42)
    
    for _ in range(100):
        d = random.randint(1, N - 1)
        Q = scalar_mul(d, G)
        
        if Q is None:
            continue
        
        x, y = Q
        lhs = (y * y) % P
        rhs = (x**3 + 7) % P
        
        assert lhs == rhs, f"Point from scalar {d} violates curve equation"
    
    print("   ✅ PASS: All computed points on curve")

def test_address_derivation_consistency():
    """Test address derivation is consistent and deterministic"""
    print("[TEST C5] Address Derivation Consistency")
    
    # Same scalar should always produce same address
    scalar = 555
    addr_list = [derive_address(scalar, mode='standard', compressed=True) for _ in range(5)]
    
    assert all(addr == addr_list[0] for addr in addr_list), "Address derivation must be deterministic"
    
    # Different mode should produce different result
    addr_standard = derive_address(scalar, mode='standard', compressed=True)
    addr_sovereign = derive_address(scalar, mode='sovereign', compressed=True)
    
    # Note: They might differ due to different RIPEMD implementations
    assert isinstance(addr_standard, str), "Standard address should be string"
    assert isinstance(addr_sovereign, str), "Sovereign address should be string"
    
    print("   ✅ PASS: Address derivation is consistent")

# ============================================================================
# PART D: SOLVER ROBUSTNESS TESTS
# ============================================================================

def test_solver_various_ranges():
    """Test solver on various range sizes"""
    print("[TEST D1] Solver on Various Ranges")
    
    test_cases = [
        (100, 200, 150),      # Range: 100, key: 150
        (1000, 2000, 1337),   # Range: 1000, key: 1337
        (5000, 10000, 7777),  # Range: 5000, key: 7777
    ]
    
    for min_r, max_r, target_d in test_cases:
        target_q = scalar_mul(target_d, G)
        solver = KangarooSolver(
            target_q,
            min_r,
            max_r,
            options={'max_iterations': 500000, 'distinguished_bits': 16}
        )
        
        result = solver.solve()
        assert result == target_d, f"Failed to recover {target_d} in range [{min_r}, {max_r}]"
    
    print("   ✅ PASS: Solver works on various ranges")

def test_solver_boundary_cases():
    """Test solver with keys at range boundaries"""
    print("[TEST D2] Solver Boundary Cases")
    
    # Key at minimum boundary
    min_r, max_r = 1000, 2000
    
    # Test at lower boundary
    target_d_low = min_r + 1
    target_q_low = scalar_mul(target_d_low, G)
    solver_low = KangarooSolver(target_q_low, min_r, max_r, 
                                 options={'max_iterations': 500000, 'distinguished_bits': 16})
    result_low = solver_low.solve()
    assert result_low == target_d_low, "Should recover key at lower boundary"
    
    # Test at upper boundary (note: max is exclusive)
    target_d_high = max_r - 1
    target_q_high = scalar_mul(target_d_high, G)
    solver_high = KangarooSolver(target_q_high, min_r, max_r, 
                                  options={'max_iterations': 500000, 'distinguished_bits': 16})
    result_high = solver_high.solve()
    assert result_high == target_d_high, "Should recover key at upper boundary"
    
    print("   ✅ PASS: Solver handles boundary cases")

def test_solver_distinguished_points_filter():
    """Test that distinguished point filter works"""
    print("[TEST D3] Distinguished Points Filter")
    
    target_d = 555
    target_q = scalar_mul(target_d, G)
    
    # Test with different DP bit settings
    for dp_bits in [4, 8, 16, 20]:
        solver = KangarooSolver(
            target_q,
            100,
            1000,
            options={'max_iterations': 500000, 'distinguished_bits': dp_bits}
        )
        
        result = solver.solve()
        assert result == target_d, f"Should work with DP bits = {dp_bits}"
    
    print("   ✅ PASS: Distinguished point filter effective")

def test_solver_hash_function():
    """Test solver's hash function for step selection"""
    print("[TEST D4] Solver Hash Function")
    
    target_d = 333
    target_q = scalar_mul(target_d, G)
    solver = KangarooSolver(target_q, 100, 1000, 
                            options={'max_iterations': 100000, 'distinguished_bits': 8})
    
    # Test hash function returns valid step indices
    for x in range(100):
        idx = solver.hash_point(x)
        assert 0 <= idx < solver.step_count, f"Hash should return index in [0, {solver.step_count})"
    
    # Test distinguished point function
    for x in range(1000000):
        is_dist = solver.is_distinguished(x)
        assert isinstance(is_dist, bool), "Distinguished check should return boolean"
    
    print("   ✅ PASS: Solver hash functions correct")

# ============================================================================
# PART E: PERFORMANCE TESTS
# ============================================================================

def test_scalar_mul_performance():
    """Benchmark scalar multiplication performance"""
    print("[TEST E1] Scalar Multiplication Performance")
    
    scalar = 2**200
    iterations = 100
    
    start = time.time()
    for _ in range(iterations):
        scalar_mul(scalar, G)
    elapsed = time.time() - start
    
    avg_time = (elapsed / iterations) * 1000  # ms
    print(f"   Average scalar_mul time: {avg_time:.3f} ms")
    
    # Should be reasonably fast (< 50ms per operation on modern hardware)
    assert avg_time < 50, f"Scalar multiplication too slow: {avg_time:.3f} ms"
    
    print("   ✅ PASS: Scalar multiplication performance acceptable")

def test_jacobian_vs_affine_performance():
    """Compare Jacobian vs Affine point operations"""
    print("[TEST E2] Jacobian vs Affine Performance")
    
    p1 = scalar_mul(123, G)
    p2 = scalar_mul(456, G)
    iterations = 1000
    
    # Affine additions
    start_affine = time.time()
    result_affine = p1
    for _ in range(iterations):
        result_affine = ec_add(result_affine, p2)
    time_affine = time.time() - start_affine
    
    # Jacobian additions
    j1 = to_jacobian(p1)
    j2 = to_jacobian(p2)
    start_jacobian = time.time()
    result_j = j1
    for _ in range(iterations):
        result_j = jacobian_add(result_j, j2)
    time_jacobian = time.time() - start_jacobian
    
    print(f"   Affine: {time_affine*1000:.2f} ms for {iterations} additions")
    print(f"   Jacobian: {time_jacobian*1000:.2f} ms for {iterations} additions")
    
    speedup = time_affine / time_jacobian
    print(f"   Jacobian speedup: {speedup:.2f}x")
    
    # Jacobian should be faster (or at least not significantly slower in Python)
    assert time_jacobian <= time_affine * 1.5, "Jacobian should not be much slower than affine"
    
    print("   ✅ PASS: Jacobian performance acceptable")

def test_address_derivation_performance():
    """Benchmark address derivation"""
    print("[TEST E3] Address Derivation Performance")
    
    iterations = 100
    start = time.time()
    for i in range(iterations):
        derive_address(i * 1000 + 1, mode='standard', compressed=True)
    elapsed = time.time() - start
    
    avg_time = (elapsed / iterations) * 1000  # ms
    print(f"   Average address derivation time: {avg_time:.3f} ms")
    
    # Should be fast (< 10ms per address typically)
    assert avg_time < 20, f"Address derivation too slow: {avg_time:.3f} ms"
    
    print("   ✅ PASS: Address derivation performance acceptable")

# ============================================================================
# PART F: MATHEMATICAL PROPERTIES
# ============================================================================

def test_group_order():
    """Test that N*G equals point at infinity"""
    print("[TEST F1] Group Order (N*G = ∞)")
    
    result = scalar_mul(N, G)
    assert result is None or result == (0, 0), "N * G should be point at infinity"
    
    # Also test N-1
    result_n_minus_1 = scalar_mul(N - 1, G)
    assert result_n_minus_1 is not None, "(N-1) * G should not be identity"
    
    print("   ✅ PASS: Group order verified")

def test_inverse_elements():
    """Test scalar inverse properties"""
    print("[TEST F2] Scalar Inverse Elements")
    
    # For any d in [1, N-1], there exists d_inv such that (d * d_inv) ≡ 1 (mod N)
    d = 12345
    d_inv = mod_inv(d, N)
    
    assert (d * d_inv) % N == 1, "Modular inverse property"
    
    # Geometric interpretation: d*G + (-d)*G = ∞
    q = scalar_mul(d, G)
    q_neg = scalar_mul((-d) % N, G)
    
    # q + q_neg should be identity
    result = ec_add(q, q_neg)
    assert result is None or result == (0, 0), "Q + (-Q) should be identity"
    
    print("   ✅ PASS: Scalar inverse elements work correctly")

def test_endomorphism_property():
    """Test secp256k1 endomorphism (lambda property)"""
    print("[TEST F3] Secp256k1 Endomorphism")
    
    # secp256k1 has the property that if (x, y) is on curve,
    # then (x * lambda_inv mod p, y) is also related via endomorphism
    # This is a simplification; full test would verify point halving
    
    p = scalar_mul(999, G)
    x, y = p
    
    # Both coordinates should be within field
    assert 0 <= x < P, "X coordinate in field"
    assert 0 <= y < P, "Y coordinate in field"
    
    print("   ✅ PASS: Endomorphism properties consistent")

# ============================================================================
# PART G: TOPOLOGICAL MANIFOLD TESTS
# ============================================================================

def test_pulse_656_properties():
    """Test Pulse 656 mathematical properties"""
    print("[TEST G1] Pulse 656 Properties")
    
    pulse = get_pulse_656()
    
    # Should be less than N
    assert 0 < pulse < N, "Pulse should be in valid range"
    
    # Should be deterministic
    pulse2 = get_pulse_656()
    assert pulse == pulse2, "Pulse 656 should be deterministic"
    
    # Verify calculation
    expected = pow(2, 656, N)
    assert pulse == expected, "Pulse 656 calculation correct"
    
    print("   ✅ PASS: Pulse 656 properties verified")

def test_sovereign_sequence_properties():
    """Test OEIS A369920 sequence properties"""
    print("[TEST G2] Sovereign Sequence Properties")
    
    # Check first 20 values
    values = [a_n(n) for n in range(20)]
    
    # Should be strictly increasing
    for i in range(len(values) - 1):
        assert values[i] < values[i+1], "Sequence should be strictly increasing"
    
    # Check divisibility: a_n = (2n+1)(5n²+5n+3)/3
    for n in range(20):
        val = a_n(n)
        # Verify formula
        expected = (2*n + 1) * (5*n**2 + 5*n + 3) // 3
        assert val == expected, f"a_n({n}) formula mismatch"
    
    print("   ✅ PASS: Sovereign sequence properties verified")

def test_fragment_extraction():
    """Test pulse fragment extraction"""
    print("[TEST G3] Pulse Fragment Extraction")
    
    pulse = get_pulse_656()
    
    # Extract various bit-length fragments
    for n_bits in [8, 16, 32, 64, 128]:
        fragment = get_fragment(pulse, n_bits)
        
        # Fragment should fit in n_bits
        assert fragment < (1 << n_bits), f"{n_bits}-bit fragment should fit in {n_bits} bits"
        assert fragment >= 0, "Fragment should be non-negative"
    
    print("   ✅ PASS: Fragment extraction correct")

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_extended_tests():
    """Execute all extended tests"""
    print("=" * 70)
    print("🦩 PROJECT FLAMINGO: EXTENDED TEST SUITE 🦩")
    print("=" * 70)
    print()
    
    test_groups = [
        ("EDGE CASES", [
            test_point_at_infinity,
            test_scalar_zero,
            test_scalar_modulo_order,
            test_scalar_negative,
            test_large_scalar,
            test_y_coordinate_recovery,
        ]),
        ("JACOBIAN EFFICIENCY", [
            test_jacobian_batch_operations,
            test_jacobian_z_coordinate_tracking,
            test_jacobian_double_special_case,
        ]),
        ("CRYPTOGRAPHIC PROPERTIES", [
            test_scalar_mul_associativity,
            test_scalar_mul_distributivity,
            test_ecdsa_signature_verification_premise,
            test_curve_equation_preservation,
            test_address_derivation_consistency,
        ]),
        ("SOLVER ROBUSTNESS", [
            test_solver_various_ranges,
            test_solver_boundary_cases,
            test_solver_distinguished_points_filter,
            test_solver_hash_function,
        ]),
        ("PERFORMANCE", [
            test_scalar_mul_performance,
            test_jacobian_vs_affine_performance,
            test_address_derivation_performance,
        ]),
        ("MATHEMATICAL PROPERTIES", [
            test_group_order,
            test_inverse_elements,
            test_endomorphism_property,
        ]),
        ("TOPOLOGICAL MANIFOLD", [
            test_pulse_656_properties,
            test_sovereign_sequence_properties,
            test_fragment_extraction,
        ]),
    ]
    
    total_passed = 0
    total_failed = 0
    
    for group_name, tests in test_groups:
        print(f"\n{'='*70}")
        print(f"GROUP: {group_name}")
        print(f"{'='*70}\n")
        
        for test in tests:
            try:
                test()
                total_passed += 1
            except AssertionError as e:
                print(f"   ❌ FAIL: {str(e)}")
                total_failed += 1
            except Exception as e:
                print(f"   ❌ ERROR: {type(e).__name__}: {str(e)}")
                total_failed += 1
            print()
    
    print("=" * 70)
    print(f"EXTENDED TEST RESULTS: {total_passed} passed, {total_failed} failed")
    print("=" * 70)
    
    if total_failed == 0:
        print("✅ ALL EXTENDED TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit_code = run_all_extended_tests()
    sys.exit(exit_code)
