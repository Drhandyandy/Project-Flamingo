import hashlib
import secrets

# --- FLAMINGO CRYPTOGRAPHIC FORMATTER ---
# Corrected to handle 71-Bit Range Validation

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def base58_encode(b_array):
    n = int.from_bytes(b_array, 'big')
    if n == 0:
        return ALPHABET[0]
    res = []
    while n > 0:
        n, r = divmod(n, 58)
        res.append(ALPHABET[r])
    res = ''.join(res[::-1])
    
    pad = 0
    for byte in b_array:
        if byte == 0: pad += 1
        else: break
    return (ALPHABET[0] * pad) + res

def generate_true_wif(hex_scalar, label="Unknown"):
    print(f"\n--- ANALYZING: {label} ---")
    print(f"[*] Raw Input Scalar: {hex_scalar}")
    
    # Validate Bit Length
    val = int(hex_scalar, 16)
    bit_len = val.bit_length()
    min_71 = 2**70
    max_71 = (2**71) - 1
    
    print(f"[*] Bit Length: {bit_len} bits")
    
    if not (min_71 <= val <= max_71):
        print(f"[!] WARNING: Scalar is OUT OF RANGE for Puzzle #71!")
        print(f"    Required: [{min_71:x} ... {max_71:x}]")
        if val < min_71:
            print(f"    Status: Too Small (Likely Puzzle #{bit_len})")
        else:
            print(f"    Status: Too Large")
    else:
        print(f"[+] VALIDATION: Scalar is within Puzzle #71 Range.")

    # Pad to exactly 64 characters (256-bit scalar)
    padded_hex = hex_scalar.zfill(64)
    
    # Prepend Sovereign Prefix 0x80 (Mainnet Uncompressed)
    payload_hex = "80" + padded_hex
    payload_bytes = bytes.fromhex(payload_hex)
    
    # Double SHA-256 Hash
    hash_1 = hashlib.sha256(payload_bytes).digest()
    hash_2 = hashlib.sha256(hash_1).digest()
    
    # Extract 4-Byte Checksum
    checksum = hash_2[:4]
    
    # Append Checksum and Encode
    final_payload = payload_bytes + checksum
    wif = base58_encode(final_payload)
    
    print(f"[+] GENERATED WIF: {wif}")
    return wif

if __name__ == "__main__":
    # 1. Test with your provided scalar (Too small)
    user_scalar = "401D4E3C2B1A0F8173"
    generate_true_wif(user_scalar, "User Input (Puzzle ~62)")
    
    # 2. Test with a valid 71-bit scalar (Randomly generated for demo)
    # Range: 2^70 to 2^71 - 1
    valid_71_bit = secrets.randbelow(2**70) + (2**70)
    valid_hex = format(valid_71_bit, 'x')
    generate_true_wif(valid_hex, "Valid 71-Bit Demo Scalar")
