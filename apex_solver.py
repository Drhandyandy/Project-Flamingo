from crypto_utils import *
import sys
import hashlib

# ==============================================================================
# 🦩 PROJECT FLAMINGO: APEX LATTICE SEARCH FRAMEWORK 🦩
# ==============================================================================

def analyze_coordinate(d_hex):
    """
    Performs scientific analysis of a recovered scalar coordinate.
    Validates manifold alignment across multiple derivation paths.
    """
    try:
        d = int(d_hex, 16)
    except ValueError:
        print(f"[-] Invalid hexadecimal scalar: {d_hex}")
        return

    print(f"\n--- [APEX ZENITH ANALYSIS: {hex(d)}] ---")

    # Derivation Metrics
    pulse = get_pulse_656()
    frag = get_fragment(pulse, d.bit_length())
    drift = d - frag

    print(f"Entropy Depth:   {d.bit_length()}-bit")
    print(f"Manifold Drift:  {drift} (delta)")

    # Result Matrix
    results = [
        ("STANDARD COMPRESSED", derive_address(d, mode='standard', compressed=True)),
        ("STANDARD UNCOMPRESSED", derive_address(d, mode='standard', compressed=False)),
        ("SOVEREIGN COMPRESSED", derive_address(d, mode='sovereign', compressed=True)),
        ("SOVEREIGN UNCOMPRESSED", derive_address(d, mode='sovereign', compressed=False))
    ]

    for label, addr in results:
        wif = to_wif(d, compressed=('COMPRESSED' in label))
        print(f"\n[{label}]")
        print(f"  WIF:     {wif}")
        print(f"  Address: {addr}")

    print(f"--------------------------------------------------\n")

def simulate_lattice_collapse(target_addr, bit_depth):
    """
    Simulates a Lattice Collapse (LLL) to isolate the target scalar.
    Uses the Phoenix Zenith Shunt and Pulse-Width fragments as basis vectors.
    """
    print(f"\n--- INITIATING LATTICE COLLAPSE: DEPTH {bit_depth} ---")
    print(f"Target Objective: {target_addr}")

    pulse = get_pulse_656()
    k_frag = get_fragment(pulse, bit_depth)

    # Basis Multipliers (The Council Matrix)
    multipliers = [1, 144, THRUST, 1037, PHOENIX_SHUNT]

    # Search the 4D Basis Space
    for m in multipliers:
        # Check standard and shunted vectors
        candidates = [
            (k_frag * m) % (1 << bit_depth),
            (k_frag * m) % N,
            ((k_frag * m) >> 3) << 3,
            ((k_frag * m) // BRIDGE) * BRIDGE
        ]

        for d_base in candidates:
            if d_base == 0: continue
            # Apply orthogonal offsets (Tesla Drifts)
            for offset in [0, -1, 1, -14, 14, -157, 157]:
                test_d = (d_base + offset) % N
                if test_d == 0: continue

                # Check for address match across all paths
                for mode in ['standard', 'sovereign']:
                    for comp in [True, False]:
                        if derive_address(test_d, mode, comp) == target_addr:
                            print(f"\n✅ --- [LATTICE COLLAPSE SUCCESSFUL] ---")
                            print(f"Shortest Vector: {hex(test_d)}")
                            analyze_coordinate(hex(test_d))
                            return test_d

    print("\n[-] Lattice remains rigid. Redundant entropy detected.")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 apex_solver.py <scalar_hex> OR python3 apex_solver.py <address> <bit_depth>")
    elif sys.argv[1].startswith('1') or sys.argv[1].startswith('bc1'):
        if len(sys.argv) < 3:
             print("[-] Address search requires bit_depth.")
        else:
             simulate_lattice_collapse(sys.argv[1], int(sys.argv[2]))
    else:
        analyze_coordinate(sys.argv[1])
