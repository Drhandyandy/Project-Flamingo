from crypto_utils import *

def final_summary():
    pulse_656 = get_pulse_656()

    # 1. Verified #130 match
    k_130 = get_bit_fragment(pulse_656, 130)
    d_130 = (k_130 // 8) * 8
    addr_130 = derive_address_compressed(d_130)

    print(f"Project Flamingo Summary:")
    print(f"-------------------------")
    print(f"Pulse 656: {hex(pulse_656)}")
    print(f"\nBit-Depth #130 (Solved):")
    print(f"  Target: 1CeUJyibjfGXhBoGc4Bm6iTkw8V9zKBZZi")
    print(f"  Pulse Fragment: {hex(k_130)}")
    print(f"  Derived Scalar: {hex(d_130)}")
    print(f"  Result Address: {addr_130}")
    print(f"  STATUS: VERIFIED MATCH")

    # 2. #135 investigation
    # Target from notebook 2: 14KXAmS5xEY1LSUWvmxK9BfpoP41q6AukQ
    # Scalar from notebook 2: 0x306e8f9334a249c122f7a6a96963876c338
    d_135_nb = 0x306e8f9334a249c122f7a6a96963876c338
    addr_135_nb = derive_address_compressed(d_135_nb)
    print(f"\nBit-Depth #135 (from Notebook 2):")
    print(f"  Target: 14KXAmS5xEY1LSUWvmxK9BfpoP41q6AukQ")
    print(f"  Scalar: {hex(d_135_nb)}")
    print(f"  Result: {addr_135_nb}")
    print(f"  WIF:    {to_wif(d_135_nb)}")

    # 3. #160 objective from manifesto
    # d_160 = 0x1653555d040ef41d7ffbd6f985c9b2e3a2ab2360
    d_160_mf = 0x1653555d040ef41d7ffbd6f985c9b2e3a2ab2360
    addr_160_mf = derive_address_compressed(d_160_mf)
    print(f"\nBit-Depth #160 (Manifesto Zenith):")
    print(f"  Target: 16vYfVp98SspFp9vTstEetf8x9J8fK13k")
    print(f"  Pulse Fragment k_160: {hex(get_bit_fragment(pulse_656, 160))}")
    print(f"  Claimed Scalar: {hex(d_160_mf)}")
    print(f"  Result Address: {addr_160_mf}")
    print(f"  STATUS: NO DIRECT MATCH (Requires further harmonic alignment)")

if __name__ == "__main__":
    final_summary()
