from crypto_utils import *
import sys

def hunt(target_addr, bit_depth, mode='standard'):
    pulse = get_pulse_656()
    k_n = get_fragment(pulse, bit_depth)
    k_v = (pulse >> (255 - bit_depth)) & ((1 << bit_depth) - 1) if bit_depth <= 255 else 0

    print(f"⚡️ PROJECT FLAMINGO: HARMONIC HUNT (#{bit_depth}) ⚡️")
    print(f"Target: {target_addr} | Mode: {mode.upper()}")

    multipliers = [1, 144, 128, 1446, 1037, 3111, 2058, 151263, 813, 157, 561, 2026]

    for s_val in [k_n, k_v]:
        if s_val == 0: continue
        for m in multipliers:
            # Test direct, floor, and shift
            candidates = [
                (s_val * m) % N,
                ((s_val * m) >> 3) << 3,
                ((s_val * m) >> 10) << 3
            ]
            for d in candidates:
                if d == 0: continue
                # Apply Tesla shift
                for offset in [0, -14, 14, -6, 6]:
                    test_d = (d + offset) % N
                    if derive_address(test_d, mode) == target_addr:
                        print(f"\n✅ [ZENITH COLLAPSE] Target Acquired!")
                        print(f"   Scalar: {hex(test_d)}")
                        print(f"   WIF:    {to_wif(test_d)}")
                        return test_d

    print("\n[-] Sector drift detected. No immediate algebraic alignment found.")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 flamingo_hunt.py <address> <bit_depth> [mode]")
    else:
        hunt(sys.argv[1], int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else 'standard')
