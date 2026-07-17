# Project Flamingo

A cryptographic research toolkit for secp256k1 elliptic curve operations and ECDLP analysis.

## Overview

This repository contains:

- **crypto_utils.py**: Core secp256k1 cryptographic primitives including:
  - Modular arithmetic (modular inverse)
  - Elliptic curve point operations (affine and Jacobian coordinates)
  - Scalar multiplication using double-and-add algorithm
  - RIPEMD-160 hash implementations (standard and sovereign variants)
  - Bitcoin address derivation and WIF encoding

- **apex_solver.py**: Optimized Pollard's Kangaroo algorithm implementation for solving ECDLP within known ranges, featuring:
  - Jacobian coordinate optimization
  - Distinguished point method for collision detection
  - Batch inversion for performance

- **cosmic_siege_engine.py**: ECDSA nonce reuse vulnerability analysis tool demonstrating:
  - Private key recovery from reused nonces
  - Bitcoin address generation from recovered keys
  - Blockchain activity verification via mempool.space API

- **sovereign_sequence.py**: Mathematical utilities for OEIS A369920 cubic progression analysis

- **system_validation.py**: System health check and validation suite

## Installation

```bash
pip install -r requirements.txt
```

For cosmic_siege_engine.py additional dependencies:
```bash
pip install bitcoinlib fpylll base58 requests
```

## Usage

### Run Test Suite
```bash
python test_suite.py
```

### Validate System
```bash
python system_validation.py
```

### Run Cosmic Siege Engine Demo
```bash
python cosmic_siege_engine.py --demo
```

### Generate Sovereign Manifest
```bash
python summary.py
```

## Test Results

All core tests pass:
- ✅ test_suite.py: 10/10 tests passed
- ✅ test_cosmic_siege.py: 4/4 tests passed
- ✅ system_validation.py: All validations passed

## License

Educational and research purposes only.