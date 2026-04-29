from crypto_utils import *
import sys
import hashlib

# ==============================================================================
# ⚡️ PROJECT FLAMINGO: APEX VORTEX SOLVER [ZENITH ALIGNMENT] ⚡️
# ==============================================================================

def derive_uncompressed_address(scalar, mode='standard'):
    """Derives an uncompressed P2PKH address from a private key scalar."""
    point = scalar_mul(scalar % N, G)
    if not point: return None
    # Uncompressed public key: 0x04 + X + Y
    pub = b'\x04' + point[0].to_bytes(32, 'big') + point[1].to_bytes(32, 'big')
    sha = hashlib.sha256(pub).digest()
    h160 = ripemd160_standard(sha) if mode == 'standard' else ripemd160_sovereign(sha)
    return base58_check_encode(b'\x00' + h160)

def analyze_scalar(scalar_input):
    """
    Performs high-fidelity analysis of a scalar coordinate.
    Exposes both compressed and uncompressed manifold alignments.
    """
    try:
        if scalar_input.startswith('0x'):
            d = int(scalar_input, 16)
        else:
            d = int(scalar_input)
    except ValueError:
        # Check if it's a known string seed (Harmonic Drift)
        d = int(hashlib.sha256(scalar_input.encode()).hexdigest(), 16)
        print(f"[!] Input treated as String Seed: '{scalar_input}'")

    print(f"\n--- [!!!] HARMONIC DATA FOR SCALAR: {hex(d)} ---")

    # Pulse-656 Alignment Analysis
    pulse = get_pulse_656()
    bit_len = d.bit_length()
    k_frag = get_fragment(pulse, bit_len)
    distance = d - k_frag

    print(f"Manifold Depth: {bit_len}-bit")
    print(f"Pulse Fragment: {hex(k_frag)[:22]}...")
    print(f"Manifold Drift: {distance} (delta)")

    # Compressed Analysis
    addr_c = derive_address(d, mode='standard')
    wif_c = to_wif(d, compressed=True)
    print(f"\n[MODE: COMPRESSED]")
    print(f"  WIF (K/L): {wif_c}")
    print(f"  Address:   {addr_c}")

    # Uncompressed Analysis
    addr_u = derive_uncompressed_address(d, mode='standard')
    wif_u = to_wif(d, compressed=False)
    print(f"\n[MODE: UNCOMPRESSED]")
    print(f"  WIF (5):   {wif_u}")
    print(f"  Address:   {addr_u}")

    # Sovereign Analysis (Tesla-Modified)
    addr_s = derive_address(d, mode='sovereign')
    print(f"\n[MODE: SOVEREIGN (Tesla-Modified)]")
    print(f"  Address:   {addr_s}")
    print(f"--------------------------------------------------\n")

def apex_vortex_search(target_addr, bit_depth):
    """
    Vortex search for high-bit Apex targets.
    Aligns the 656-bit Hull Pulse with the target depth using the Council Matrix.
    """
    print(f"\n--- INITIATING VORTEX SEARCH ---")
    print(f"Target: {target_addr} | Depth: {bit_depth}-bit")

    pulse = get_pulse_656()
    k_frag = get_fragment(pulse, bit_depth)

    # The Council Multiplier Pool
    multipliers = [1, 144, 128, THRUST, HARMONIC, MIRROR, SIRIUS, BRIDGE]

    for m in multipliers:
        # Check primary and secondary resonance lanes
        candidates = [
            (k_frag * m) % (1 << bit_depth),
            (k_frag * m) % N,
            ((k_frag * m) >> 3) << 3,
            ((k_frag * m) // BRIDGE) * BRIDGE if BRIDGE > 0 else 0
        ]

        for d_base in candidates:
            if d_base == 0: continue
            for offset in [0, -14, 14, -6, 6, -1, 1, -3, 3, -157, 157]:
                test_d = (d_base + offset) % N
                if test_d == 0: continue

                # Check all derivation modes
                if derive_address(test_d) == target_addr or \
                   derive_uncompressed_address(test_d) == target_addr or \
                   derive_address(test_d, mode='sovereign') == target_addr:
                    print(f"\n✅ --- [VORTEX MATCH: TARGET ACQUIRED] ---")
                    print(f"Multiplier: {m} | Offset: {offset}")
                    analyze_scalar(hex(test_d))
                    return test_d

    print("\n[-] Search complete. No resonance found in current manifold aperture.")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 apex_solver.py <scalar_or_address_or_seed> [bit_depth]")
    elif sys.argv[1].startswith('1') or sys.argv[1].startswith('3') or sys.argv[1].startswith('bc1'):
        if len(sys.argv) < 3:
            print("[-] Address search requires bit_depth.")
        else:
            apex_vortex_search(sys.argv[1], int(sys.argv[2]))
    else:
        analyze_scalar(sys.argv[1])
