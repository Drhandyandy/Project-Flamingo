from crypto_utils import *
import sys
import hashlib

def derive_uncompressed_address(scalar):
    """Derives an uncompressed P2PKH address from a private key scalar."""
    point = scalar_mul(scalar % N, G)
    if not point: return None
    # Uncompressed public key: 0x04 + X + Y
    pub = b'\x04' + point[0].to_bytes(32, 'big') + point[1].to_bytes(32, 'big')
    sha = hashlib.sha256(pub).digest()
    h160 = ripemd160_standard(sha)
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
        print(f"[-] Invalid scalar input: {scalar_input}")
        return

    print(f"\n--- [!!!] HARMONIC DATA FOR SCALAR: {hex(d)} ---")

    # Compressed Analysis
    addr_c = derive_address(d, mode='standard')
    wif_c = to_wif(d, compressed=True)
    print(f"\n[MODE: COMPRESSED]")
    print(f"  WIF (K/L): {wif_c}")
    print(f"  Address:   {addr_c}")

    # Uncompressed Analysis
    addr_u = derive_uncompressed_address(d)
    wif_u = to_wif(d, compressed=False)
    print(f"\n[MODE: UNCOMPRESSED]")
    print(f"  WIF (5):   {wif_u}")
    print(f"  Address:   {addr_u}")
    print(f"--------------------------------------------------\n")

def apex_vortex_search(target_addr, bit_depth):
    """
    Vortex search for high-bit Apex targets (#160, #140).
    Aligns the 656-bit Hull Pulse with the target depth.
    """
    print(f"\n--- INITIATING VORTEX SEARCH ---")
    print(f"Target: {target_addr} | Depth: {bit_depth}-bit")

    pulse = get_pulse_656()
    # Fragment around the depth
    k_frag = get_fragment(pulse, bit_depth)
    print(f"Pulse Fragment: {hex(k_frag)}")

    # We apply the Council Multipliers to the fragment
    multipliers = [1, 144, 128, THRUST, HARMONIC, MIRROR, SIRIUS]

    for m in multipliers:
        for shift in [0, 3, -3, 10, -10]:
            d_base = (k_frag * m) % N
            if shift > 0: d_base >>= shift
            elif shift < 0: d_base <<= abs(shift)

            for offset in [0, -14, 14, -6, 6]:
                test_d = (d_base + offset) % N
                if test_d == 0: continue

                # Check both compressed and uncompressed
                if derive_address(test_d) == target_addr or derive_uncompressed_address(test_d) == target_addr:
                    print(f"\n✅ --- [VORTEX MATCH: TARGET ACQUIRED] ---")
                    analyze_scalar(hex(test_d))
                    return test_d

    print("\n[-] Search complete. No resonance found in this manifold.")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 apex_solver.py <scalar_or_address> [bit_depth]")
    elif sys.argv[1].startswith('1') or sys.argv[1].startswith('3') or sys.argv[1].startswith('bc1'):
        if len(sys.argv) < 3:
            print("[-] Address search requires bit_depth.")
        else:
            apex_vortex_search(sys.argv[1], int(sys.argv[2]))
    else:
        analyze_scalar(sys.argv[1])
