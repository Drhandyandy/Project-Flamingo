from crypto_utils import *
import sys

def jackrabbit_sniper_overdrive(target_addr, bit_depth, mode='standard'):
    """
    PHASE III DETRAMMELIZED EXPANSION
    Combines all Project Flamingo multipliers and Tesla offsets for surgical acquisition.
    """
    pulse = get_pulse_656()
    k_n = get_fragment(pulse, bit_depth)

    # The Vortex Boundary (255-bit lock)
    k_v = (pulse >> (255 - bit_depth)) & ((1 << bit_depth) - 1) if bit_depth <= 255 else 0

    print(f"⚡️ INITIATING JACKRABBIT SNIPER OVERDRIVE ⚡️")
    print(f"Target: {target_addr} | Depth: {bit_depth}-bit | Mode: {mode.upper()}")

    # The Council Multiplier Pool
    multipliers = [1, 144, 128, THRUST, HARMONIC, KATRINA, NATASHA, PRIMARY_7, SECONDARY_7, SIRIUS]

    # The Sovereign Search Loop
    for source_val in [k_n, k_v]:
        if source_val == 0: continue
        for m in multipliers:
            # Manifold Alignments
            candidates = [
                (source_val * m) % N,
                ((source_val * m) >> 3) << 3,
                ((source_val * m) >> 10) << 3,
                (source_val * m * inv(BRIDGE, N)) % N if BRIDGE > 0 else 0
            ]

            for d_base in candidates:
                # Apply Tesla Drifts/Offsets
                for offset in [0, -14, 14, -6, 6]:
                    test_d = (d_base + offset) % N
                    if test_d == 0: continue

                    if derive_address(test_d, mode) == target_addr:
                        print(f"\n✅ --- [ZENITH COLLAPSE: TARGET ACQUIRED] ---")
                        print(f"Multiplier: {m} | Offset: {offset}")
                        print(f"Final Scalar: {hex(test_d)}")
                        print(f"WIF:          {to_wif(test_d)}")
                        return test_d

    print("\n[-] Sector remains resistant. Increasing Swarm Density recommended.")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 flamingo_hunt.py <address> <bit_depth> [mode]")
    else:
        jackrabbit_sniper_overdrive(sys.argv[1], int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else 'standard')
