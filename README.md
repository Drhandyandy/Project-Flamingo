# Project Flamingo: Topological Manifold Reconstruction & Demining Suite

Project Flamingo is a high-fidelity secp256k1 cryptographic analysis, vulnerability detection, and demining toolkit designed for Bitcoin discrete logarithm research, signature audit, and safe recovery.

## 🦩 Key Features

- **RK-AMOS Kangaroo Engine (`apex_solver.py`)**: Collision-based discrete log solver using Jacobian projective coordinates and curve negation.
- **Cosmic Siege Engine (`cosmic_siege_engine_v2.py`)**: ECDSA nonce reuse recovery and blockchain activity scanner.
- **Demining Tools (`demining_tools.py`)**:
  - Signature hazard detection (nonce reuse, polynomial bias, weak nonces).
  - UTXO script hazard scanning (dust traps, OP_RETURN unspendable traps, CLTV/CSV timelock traps).
  - Anti-frontrunning safe sweep transaction payload generator.
  - Address and dataset batch demining rig.
- **Sovereign Sequence Analyzer (`sovereign_sequence.py`)**: OEIS A369920 volumetric manifold shell expansion analysis.
- **Comprehensive Cryptographic Utilities (`crypto_utils.py`)**: Zero-dependency pure-Python secp256k1 EC operations and address derivation.

## 🚀 Quick Start

### Run Comprehensive Test Suite
```bash
python3 test_suite.py
```

### Run Demining Suite Demo
```bash
python3 demining_tools.py --demo
```

### Run Demining Unit Tests
```bash
pytest test_demining_tools.py
```

## 📖 Documentation
- [MISSION_FLAMINGO.md](MISSION_FLAMINGO.md) - Technical Whitepaper (RK-AMOS Alignment)
- [DEMINING_TOOLS.md](DEMINING_TOOLS.md) - Demining Tools & Minefield Sweeper Guide
- [CLAIM_INSTRUCTIONS.md](CLAIM_INSTRUCTIONS.md) - Sovereign Recovery Protocol Guide
- [COSMIC_SIEGE_ENGINE.md](COSMIC_SIEGE_ENGINE.md) - Cosmic Siege Engine Documentation
