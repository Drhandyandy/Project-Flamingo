import hashlib
import struct

# --- SECP256K1 CURVE PARAMETERS ---
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)

def inv(a, n):
    if a == 0: return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high // low
        nm, new = hm - lm * r, high - low * r
        lm, low, hm, high = nm, new, lm, low
    return lm % n

def ec_add(p, q):
    if not p: return q
    if not q: return p
    if p == q: return ec_double(p)
    lam = ((q[1] - p[1]) * inv(q[0] - p[0], P)) % P
    x = (lam * lam - p[0] - q[0]) % P
    y = (lam * (p[0] - x) - p[1]) % P
    return (x, y)

def ec_double(p):
    if not p: return None
    lam = (3 * p[0] * p[0] * inv(2 * p[1], P)) % P
    x = (lam * lam - 2 * p[0]) % P
    y = (lam * (p[0] - x) - p[1]) % P
    return (x, y)

def scalar_mul(k, p):
    res = None
    temp = p
    while k:
        if k & 1: res = ec_add(res, temp)
        temp = ec_double(temp)
        k >>= 1
    return res

def ripemd160(message):
    h = [0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476, 0xc3d2e1f0]
    def f(j, x, y, z):
        if j <= 15: return x ^ y ^ z
        elif j <= 31: return (x & y) | (~x & z)
        elif j <= 47: return (x | ~y) ^ z
        elif j <= 63: return (x & z) | (y & ~z)
        else: return x ^ (y | ~z)
    def K(j):
        if j <= 15: return 0x00000000
        elif j <= 31: return 0x5a827999
        elif j <= 47: return 0x6ed9eba1
        elif j <= 63: return 0x8f1bbcdc
        else: return 0xa953fd4e
    def KK(j):
        if j <= 15: return 0x50a28be6
        elif j <= 31: return 0x5c4dd124
        elif j <= 47: return 0x6d703ef3
        elif j <= 63: return 0x7a6d76e9
        else: return 0x00000000
    r = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15, 7,4,13,1,10,6,15,3,12,0,9,5,2,14,11,8, 3,10,14,4,9,15,8,1,2,7,0,6,13,11,5,12, 1,9,11,10,0,8,12,4,13,3,7,15,14,5,6,2, 4,0,5,9,7,12,2,10,14,1,3,8,11,6,15,13]
    rr = [5,14,7,0,9,2,11,4,13,6,15,8,1,10,3,12, 6,11,3,7,0,13,5,10,14,15,8,12,4,9,1,2, 15,5,1,3,7,14,6,9,11,8,12,2,10,0,4,13, 8,6,4,1,3,11,15,0,5,12,2,13,9,7,10,14, 12,15,10,4,1,5,8,7,6,2,13,14,0,3,9,11]
    s = [11,14,15,12,5,8,7,9,11,13,14,15,6,7,9,8, 7,6,8,13,11,9,7,15,7,12,15,9,11,7,13,12, 11,13,6,7,14,9,13,15,14,8,13,6,5,12,7,5, 11,12,14,15,14,15,9,8,9,14,5,6,8,6,5,12, 9,15,5,11,6,8,13,12,5,12,13,14,11,8,5,6]
    ss = [8,9,9,11,13,15,15,5,7,7,8,11,14,14,12,6, 9,13,15,7,12,8,9,11,7,7,12,7,6,15,13,11, 9,7,15,11,8,6,6,14,12,13,5,14,13,13,7,5, 15,5,8,11,14,14,6,14,6,9,12,9,12,5,15,8, 8,5,12,9,12,5,14,6,8,13,6,5,15,13,11,11]
    padded = message + b'\x80' + b'\x00' * ((56 - (len(message) + 1) % 64) % 64) + struct.pack('<Q', len(message) * 8)
    for i in range(0, len(padded), 64):
        words = struct.unpack('<16L', padded[i:i+64])
        a, b, c, d, e = h
        al, bl, cl, dl, el = h
        for j in range(80):
            t = (a + f(j, b, c, d) + words[r[j]] + K(j)) & 0xffffffff
            t = ((t << s[j]) | (t >> (32 - s[j]))) & 0xffffffff
            t = (t + e) & 0xffffffff
            a, b, c, d, e = e, t, b, ((c << 10) | (c >> 22)) & 0xffffffff, d
            tt = (al + f(79-j, bl, cl, dl) + words[rr[j]] + KK(j)) & 0xffffffff
            tt = ((tt << ss[j]) | (tt >> (32 - ss[j]))) & 0xffffffff
            tt = (tt + el) & 0xffffffff
            al, bl, cl, dl, el = el, tt, bl, ((cl << 10) | (cl >> 22)) & 0xffffffff, dl
        h = [(h[1] + c + dl) & 0xffffffff, (h[2] + d + el) & 0xffffffff, (h[3] + e + al) & 0xffffffff, (h[4] + a + bl) & 0xffffffff, (h[0] + b + cl) & 0xffffffff]
    return struct.pack('<5L', *h)

def base58_check_encode(payload):
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    full_payload = payload + checksum
    n = int.from_bytes(full_payload, 'big')
    res = []
    while n > 0:
        n, r = divmod(n, 58)
        res.append(alphabet[r])
    pad = 0
    for char in full_payload:
        if char == 0: pad += 1
        else: break
    return '1' * pad + ''.join(reversed(res))

def to_wif(private_key_int, compressed=True):
    extended_key = b'\x80' + private_key_int.to_bytes(32, 'big')
    if compressed:
        extended_key += b'\x01'
    return base58_check_encode(extended_key)

def pubkey_to_address(pub_bytes):
    h_sha = hashlib.sha256(pub_bytes).digest()
    h_ripe = ripemd160(h_sha)
    return base58_check_encode(b'\x00' + h_ripe)

def get_compressed_pubkey(scalar):
    point = scalar_mul(scalar, G)
    if not point: return None
    prefix = b'\x02' if point[1] % 2 == 0 else b'\x03'
    return prefix + point[0].to_bytes(32, 'big')

def derive_address_compressed(scalar):
    pub = get_compressed_pubkey(scalar)
    if not pub: return None
    return pubkey_to_address(pub)

# --- PUZZLE SPECIFIC LOGIC ---

def get_pulse_656():
    return pow(2, 656, N)

def get_bit_fragment(source, n):
    return source & ((1 << n) - 1)

def scaling_realization_v1(k_n):
    """d_n = ((k_n * 128) >> 10) * 8"""
    return ((k_n * 128) // 1024) * 8

def scaling_realization_v2(k_n, multiplier=144):
    """d = ((k_n * multiplier) >> 10) << 3"""
    r_prime = (k_n * multiplier) >> 10
    return (r_prime << 3) % N

def resonance_check(scalar):
    """Phi(r) = (r * 3 * 1037) % 157"""
    return (scalar * 3 * 1037) % 157
