from crypto_utils import *
import sys

def search_pulse_resonance(target_addr, bit_depth, multiplier_range=None, offset_radius=1000):
    """
    Unified search tool for puzzle resonance alignment.
    Incorporates the Scaling Realization, Tesla offsets, and Volumetric Swarm factors.
    """
    pulse_656 = get_pulse_656()
    k_n = get_bit_fragment(pulse_656, bit_depth)

    # User's Precision Constants
    THRUST = 1446
    HARMONIC = 1037
    MIRROR = 157
    PRIMARY_FACTOR = (7**3) * 6
    SECONDARY_FACTOR = (7**5) * 9

    print(f"--- PROJECT FLAMINGO: RESONANCE SCAN ---")
    print(f"Target: {target_addr} (Depth #{bit_depth})")
    print(f"Source: {hex(k_n)}")

    # 1. Primary Resonance Check (Tesla/Nike Alignment)
    # Using the 1446 Thrust and 1037 Harmonic
    for m in [THRUST, HARMONIC, PRIMARY_FACTOR, SECONDARY_FACTOR, 144, 128]:
        # Q10 Scaling: d = ((k * m) >> 10) << 3
        d_scaled = ((k_n * m) >> 10) << 3
        if derive_address_compressed(d_scaled % N) == target_addr:
            print(f"\n[!!!] HARMONIC MATCH: THRUST ALIGNED!")
            print(f"Multiplier: {m} | Scalar: {hex(d_scaled % N)}")
            return d_scaled % N

    # 2. Check Standard Scaling (Floor)
    d_floor = (k_n // 8) * 8
    if derive_address_compressed(d_floor) == target_addr:
        print(f"\n[!!!] HIT: Scaling V1 (Standard Floor)")
        print(f"Scalar: {hex(d_floor)}")
        return d_floor

    # 3. Systematic Multiplier Search
    print("\nScanning harmonic field...")
    search_multipliers = multiplier_range if multiplier_range else [128, 144, THRUST, HARMONIC, PRIMARY_FACTOR]

    for m in search_multipliers:
        # Check Direct and Q10 alignments
        for shift_right in [10, 0]:
            d_base = (k_n * m) >> shift_right
            for shift_left in [0, 3]:
                d_aligned = (d_base << shift_left) % N
                if d_aligned == 0: continue

                # Check for address match around resonance point
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
