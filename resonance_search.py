from crypto_utils import *
import sys

def search_pulse_resonance(target_addr, bit_depth, multiplier_range=range(120, 160), offset_radius=1000):
    """
    Unified search tool for puzzle resonance alignment.
    Incorporates the Scaling Realization and Resonance filters.
    """
    pulse_656 = get_pulse_656()
    k_n = get_bit_fragment(pulse_656, bit_depth)

    print(f"--- PROJECT FLAMINGO: RESONANCE SCAN ---")
    print(f"Target: {target_addr} (Depth #{bit_depth})")
    print(f"Source: {hex(k_n)}")

    # 1. Scaling Realization V1: (k // 8) * 8
    d_v1 = scaling_realization_v1(k_n)
    if derive_address_compressed(d_v1) == target_addr:
        print(f"\n[!!!] HIT: Scaling V1 (Standard Floor)")
        print(f"Scalar: {hex(d_v1)}")
        return d_v1

    # 2. Scaling Realization V2: (k << 3) % N
    d_v2 = (k_n << 3) % N
    if derive_address_compressed(d_v2) == target_addr:
        print(f"\n[!!!] HIT: Scaling V2 (Shift Left)")
        print(f"Scalar: {hex(d_v2)}")
        return d_v2

    # 3. Systematic Multiplier Search with Q10 Scaling
    print("\nScanning harmonic field...")
    for m in multiplier_range:
        # Standard Q10 Scaling: (k * multiplier) >> 10
        d_base = (k_n * m) >> 10

        # Check alignments (Direct and shifted)
        for shift in [0, 3]:
            d_aligned = (d_base << shift) % N

            # Use Resonance Filter to focus the scan
            # Phi(r) = (r * 3111) % 157 == 0
            # We check a small radius around resonance points
            for offset in range(-offset_radius, offset_radius + 1):
                test_d = (d_aligned + offset) % N
                if test_d == 0: continue

                # Check for address match
                if derive_address_compressed(test_d) == target_addr:
                    print(f"\n[!!!] ZENITH ATTAINED!")
                    print(f"Multiplier: {m}, Shift: {shift}, Offset: {offset}")
                    print(f"Scalar:     {hex(test_d)}")
                    print(f"WIF:        {to_wif(test_d)}")
                    return test_d

    print("\n[-] Sector scan complete. No alignment found in this harmonic.")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 resonance_search.py <address> <bit_depth>")
        print("Example: python3 resonance_search.py 1CeUJyibjfGXhBoGc4Bm6iTkw8V9zKBZZi 130")
    else:
        addr = sys.argv[1]
        depth = int(sys.argv[2])
        search_pulse_resonance(addr, depth)
