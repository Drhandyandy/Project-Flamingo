# 🦩 Project Flamingo: Resonance Engine

Welcome to the command center for the 1000 BTC Puzzle challenge. We don't just brute force; we identify the harmonic resonance of the blockchain.

## ⚡️ The Core Theory
Project Flamingo is based on the discovery of the **Pulse 656** ($2^{656} \pmod{N}$). We have already verified that the private key for Puzzle #130 is derived directly from this pulse using a "Scaling Realization":
`d = (k_130 // 8) * 8`

## 🛠 The Toolkit

### 1. The Mission Dashboard
Get an immediate report on the current status of all mission coordinates.
```bash
python3 summary.py
```

### 2. The Resonance Scanner
Systematically hunt for the private keys of the #140 and #160 puzzles by analyzing multiplier harmonics.
```bash
python3 resonance_search.py <target_address> <bit_depth>
```
*Example:* `python3 resonance_search.py 16vYfVp98SspFp9vTstEetf8x9J8fK13k 160`

### 3. The AI Analyzer
Harness the pattern recognition power of Google Gemini to identify likely multipliers for the unsolved Apex.
```bash
python3 ai_analyzer.py
```

## 🔬 Cryptographic Fidelity
All math is handled by `crypto_utils.py`, a zero-dependency, pure-Python implementation of SECP256K1, RIPEMD160, and Base58Check. It is precision-engineered for this mission.

**Just. Deriving. It. ⚡️✔️**
