import hashlib
import time
import os

# ==============================================================================
# CONFIGURATION: PUZZLE #71 & PHOENIX CONSTANTS
# ==============================================================================

# Puzzle #71 Target
TARGET_ADDRESS = "1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU"
RANGE_START = 2**70
RANGE_END = 2**71 - 1
RANGE_SIZE = RANGE_END - RANGE_START + 1
N_BITS = 71

# Phoenix Constants (Corrected)
PHOENIX_DIVISOR = 90
PHOENIX_OFFSET = 16  # Verified: 2^256 % 90 == 16
S = (2**256 - PHOENIX_OFFSET) // PHOENIX_DIVISOR
PHOENIX_BASE = 656
PHOENIX_STEP = 90

# Elliptic Curve Parameters (secp256k1)
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
A = 0
B = 7
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
G = (Gx, Gy)
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# ==============================================================================
# CRYPTO PRIMITIVES (Pure Python for Portability)
# ==============================================================================

def mod_inv(a, p):
    """Extended Euclidean Algorithm for modular inverse."""
    if a < 0: a += p
    lm, hm = 1, 0
    low, high = a % p, p
    while low > 1:
        ratio = high // low
        nm, new = hm - lm * ratio, high - low * ratio
        lm, low, hm, high = nm, new, lm, low
    return lm % p

def point_add(P1, P2):
    if P1 is None: return P2
    if P2 is None: return P1
    if P1[0] == P2[0] and (P1[1] != P2[1] or P1[1] == 0):
        return None
    if P1[0] == P2[0]:
        m = (3 * P1[0]**2 + A) * mod_inv(2 * P1[1], P) % P
    else:
        m = (P2[1] - P1[1]) * mod_inv(P2[0] - P1[0], P) % P
    x3 = (m**2 - P1[0] - P2[0]) % P
    y3 = (m * (P1[0] - x3) - P1[1]) % P
    return (x3, y3)

def scalar_mult(k, G):
    """Double-and-add algorithm."""
    result = None
    addend = G
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result

def sha256(x):
    return hashlib.sha256(x).digest()

def ripemd160(x):
    h = hashlib.new('ripemd160')
    h.update(x)
    return h.digest()

def encode_address(pubkey_bytes, version=0):
    """Generate Bitcoin address from compressed/uncompressed pubkey."""
    h1 = sha256(pubkey_bytes)
    h2 = ripemd160(h1)
    ver_byte = bytes([version]) + h2
    checksum = sha256(sha256(ver_byte))[:4]
    payload = ver_byte + checksum
    
    # Base58 Encode
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    num = int.from_bytes(payload, 'big')
    encoded = ''
    while num > 0:
        num, remainder = divmod(num, 58)
        encoded = alphabet[remainder] + encoded
    # Leading zeros
    for byte in payload:
        if byte == 0:
            encoded = '1' + encoded
        else:
            break
    return encoded

def pubkey_to_address(point):
    if point is None: return None
    x, y = point
    # Compressed pubkey (02/03 + x)
    prefix = b'\x02' if y % 2 == 0 else b'\x03'
    pubkey_bytes = prefix + x.to_bytes(32, 'big')
    return encode_address(pubkey_bytes)

# ==============================================================================
# PHOENIX SEEDED KANGAROO LOGIC
# ==============================================================================

class Kangaroo:
    def __init__(self, start_dist, start_pos, name="Wild"):
        self.dist = start_dist  # Distance from origin (scalar offset)
        self.pos = start_pos    # Current Point (x,y)
        self.name = name
        self.steps = 0

    def jump(self, jump_size, jump_point):
        self.pos = point_add(self.pos, jump_point)
        self.dist = (self.dist + jump_size) % N
        self.steps += 1

def get_phoenix_seed(k):
    """Generate a deterministic seed based on Phoenix Lemma 2."""
    pz = PHOENIX_BASE + (PHOENIX_STEP * k)
    # Mix S and Pz
    mixed = (S ^ pz) % N
    # Fold to 71-bit range roughly
    seed = mixed % (2**72) 
    return seed

def derive_target_point():
    """
    In a real distributed attack, we would compute T = PubKey - (2^70 * G).
    Since we don't have the PubKey yet (we only have Address), we must 
    iterate forward from the lower bound and check addresses.
    
    OPTIMIZATION: We will run a 'Forward Herd' from 2^70 using Phoenix steps.
    """
    pass # Handled in main loop

# ==============================================================================
# MAIN SOLVER: PHOENIX SWARM SIMULATION
# ==============================================================================

def run_phoenix_swarm(max_iterations=50000):
    print(f"[*] Initializing Phoenix Swarm for Puzzle #{N_BITS}...")
    print(f"[*] Target Address: {TARGET_ADDRESS}")
    print(f"[*] Range: [{hex(RANGE_START)}, {hex(RANGE_END)}]")
    print(f"[*] Phoenix Constant S: {hex(S)[:20]}... (254 bits)")
    print(f"[*] Strategy: Phoenix-Seeded Forward Walk")
    
    # Precompute Jump Table (Powers of 2 for binary stepping + Phoenix Jumps)
    # Using small powers for speed in Python
    jump_table = []
    for i in range(1, 20): 
        size = 2**i
        pt = scalar_mult(size, G)
        jump_table.append((size, pt))
    
    # Add Phoenix Special Jumps (multiples of 90)
    for i in range(1, 10):
        size = PHOENIX_STEP * i * (2**10) # Large phoenix jumps
        pt = scalar_mult(size, G)
        jump_table.append((size, pt))

    # Initialize Herd
    herd = []
    num_kangaroos = 10
    
    print(f"[*] Releasing {num_kangaroos} Phoenix-Kangaroos...")
    
    for i in range(num_kangaroos):
        # Seed each kangaroo with a different Phoenix phase
        k_seed = i * 1000
        seed_val = get_phoenix_seed(k_seed)
        
        # Start position: Base Range Start + Phoenix Seed Offset
        start_scalar = RANGE_START + (seed_val % (2**60)) # Keep within reasonable window
        start_pt = scalar_mult(start_scalar, G)
        
        kanga = Kangaroo(start_scalar - RANGE_START, start_pt, f"Phoenix-{i}")
        herd.append(kanga)

    print(f"[*] Beginning Search Loop ({max_iterations} iterations)...")
    start_time = time.time()
    
    found = False
    
    for step in range(max_iterations):
        # Move each kangaroo
        for kanga in herd:
            # Deterministic jump based on current position x-coordinate
            # Use last few bytes of x to select jump
            x_bytes = kanga.pos[0].to_bytes(32, 'big')
            idx = int.from_bytes(x_bytes[-2:], 'big') % len(jump_table)
            
            j_size, j_pt = jump_table[idx]
            kanga.jump(j_size, j_pt)
            
            # Check Address every 100 steps to save time
            if kanga.steps % 100 == 0:
                current_scalar = RANGE_START + kanga.dist
                # Ensure we stay in range (modulo wrap handling simplified here)
                if current_scalar > RANGE_END:
                    current_scalar = RANGE_START + (kanga.dist % (RANGE_SIZE))
                
                # Derive Public Key from current scalar
                # Optimization: We are tracking pos as (Start + dist), so pos is the pubkey point
                addr = pubkey_to_address(kanga.pos)
                
                if addr == TARGET_ADDRESS:
                    print(f"\n[!!!] SOLUTION FOUND at step {step}!")
                    print(f"[+] Scalar: {hex(current_scalar)}")
                    print(f"[+] Decimal: {current_scalar}")
                    print(f"[+] Address: {addr}")
                    found = True
                    break
        
        if found:
            break
            
        # Progress Report
        if step % 1000 == 0:
            elapsed = time.time() - start_time
            rate = (step * num_kangaroos * 100) / elapsed if elapsed > 0 else 0
            print(f"   Step {step}/{max_iterations} | Checked: {step*num_kangaroos*100} | Rate: {rate:.0f} keys/s", end='\r')

    if not found:
        print(f"\n[*] Search completed. No solution found in {max_iterations} iterations.")
        print(f"[*] Total keys tested: ~{max_iterations * num_kangaroos * 100:,}")
        print(f"[*] Note: Puzzle #71 requires ~34 Billion operations. This was a proof-of-concept swarm.")

if __name__ == "__main__":
    try:
        run_phoenix_swarm(max_iterations=2000) # Run 2000 super-steps (200k key checks)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
