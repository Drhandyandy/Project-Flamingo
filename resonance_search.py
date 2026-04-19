from crypto_utils import *
import sys

def search_pulse_resonance(target_addr, bit_depth, multiplier_range=None, offset_radius=1000):
    """
    Unified search tool for puzzle resonance alignment.
    Incorporates the Scaling Realization and specific Harmonic Factors.
    """
    pulse_656 = get_pulse_656()
    k_n = get_bit_fragment(pulse_656, bit_depth)

    print(f"--- PROJECT FLAMINGO: RESONANCE SCAN ---")
    print(f"Target: {target_addr} (Depth #{bit_depth})")
    print(f"Source: {hex(k_n)}")

    # 1. Primary Resonance (Tesla/Nike Alignment): 7^3 * 6
    primary_multiplier = (7**3) * 6
    d_primary = (k_n * primary_multiplier) % N
    if derive_address_compressed(d_primary) == target_addr:
        print(f"\n[!!!] PRIMARY HARMONIC MATCH: SOLVE TRIGGER!")
        print(f"Scalar: {hex(d_primary)}")
        print(f"WIF:    {to_wif(d_primary)}")
        return d_primary

    # 2. Secondary Resonance (Vector Alignment): 7^5 * 9
    secondary_multiplier = (7**5) * 9
    d_secondary = (k_n * secondary_multiplier) % N
    if derive_address_compressed(d_secondary) == target_addr:
        print(f"\n[!!!] SECONDARY HARMONIC MATCH: VECTOR ALIGNMENT!")
        print(f"Scalar: {hex(d_secondary)}")
        print(f"WIF:    {to_wif(d_secondary)}")
        return d_secondary

    # 3. Standard Scaling (Floor)
    d_floor = (k_n // 8) * 8
    if derive_address_compressed(d_floor) == target_addr:
        print(f"\n[!!!] HIT: Scaling V1 (Standard Floor)")
        print(f"Scalar: {hex(d_floor)}")
        return d_floor

    # 4. Systematic Multiplier Search
    print("\nScanning harmonic field...")
    search_multipliers = multiplier_range if multiplier_range else [128, 144, primary_multiplier, secondary_multiplier]

    for m in search_multipliers:
        # Standard Q10 Scaling or Direct Multiplier
        for shift_right in [10, 0]:
            d_base = (k_n * m) >> shift_right

            for shift_left in [0, 3]:
                d_aligned = (d_base << shift_left) % N
                if d_aligned == 0: continue

                # Broad radius around resonance points
                for offset in range(-offset_radius, offset_radius + 1):
                    test_d = (d_aligned + offset) % N
                    if derive_address_compressed(test_d) == target_addr:
                        print(f"\n[!!!] RESONANCE COLLAPSE ATTAINED!")
                        print(f"Multiplier: {m}, SR: {shift_right}, SL: {shift_left}, Offset: {offset}")
                        print(f"Scalar:     {hex(test_d)}")
                        print(f"WIF:        {to_wif(test_d)}")
                        return test_d

    print("\n[-] Sector scan complete. No alignment found in this harmonic.")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 resonance_search.py <address> <bit_depth>")
        print("Example: python3 resonance_search.py 1PWo95AY7X9N8tJ2W16aAb2JvywW6V5nJ7 140")
    else:
        addr = sys.argv[1]
        depth = int(sys.argv[2])
        search_pulse_resonance(addr, depth)
