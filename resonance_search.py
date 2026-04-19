from crypto_utils import *
import sys

def search_pulse_resonance(target_addr, bit_depth, multiplier_range=range(120, 160), offset_radius=100):
    """
    Unified search tool for puzzle resonance alignment.
    """
    pulse_656 = get_pulse_656()
    k_n = get_bit_fragment(pulse_656, bit_depth)

    print(f"--- SEARCHING RESONANCE FOR DEPTH #{bit_depth} ---")
    print(f"Target Address: {target_addr}")
    print(f"Pulse Fragment: {hex(k_n)}")

    # 1. Check standard floor derivation (used in #130)
    d_std = (k_n // 8) * 8
    if derive_address_compressed(d_std) == target_addr:
        print(f"[!] DIRECT MATCH FOUND (Standard Floor Method)")
        print(f"Scalar: {hex(d_std)}")
        print(f"WIF:    {to_wif(d_std)}")
        return d_std

    # 2. Check systematically through multipliers and offsets
    for m in multiplier_range:
        d_base = (k_n * m) >> 10
        for shift in [0, 3]:
            d_shift = (d_base << shift) % N
            for offset in range(-offset_radius, offset_radius + 1):
                test_d = (d_shift + offset) % N
                if test_d == 0: continue
                if derive_address_compressed(test_d) == target_addr:
                    print(f"[!] MATCH FOUND!")
                    print(f"Multiplier: {m}, Shift: {shift}, Offset: {offset}")
                    print(f"Scalar:     {hex(test_d)}")
                    print(f"WIF:        {to_wif(test_d)}")
                    return test_d

    print("[-] No match found in specified range.")
    return None

if __name__ == "__main__":
    # Example: Run verification for #130
    search_pulse_resonance('1CeUJyibjfGXhBoGc4Bm6iTkw8V9zKBZZi', 130)

    # Check #135 from Notebook 2
    search_pulse_resonance('14KXAmS5xEY1LSUWvmxK9BfpoP41q6AukQ', 135)
