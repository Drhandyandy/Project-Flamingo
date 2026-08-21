# 🦩 Project Flamingo: Demining Tools & Minefield Sweeper

The **Demining Suite** (`demining_tools.py`) provides detection, hazard analysis, and safe recovery mechanisms for Bitcoin signatures, UTXOs, and addresses. It is designed to neutralize cryptographic traps, bad RNG "mines", script-level honeypots, and mempool front-running hazards.

---

## I. CORE DEMINING MODULES

### 1. `MineDetector` (Hazard Detection Engine)
- **Repeated Nonce Mine Detection (`check_signature_nonce_reuse`)**:
  Identifies signatures sharing identical $r$-values and automatically solves for the private key $d = \frac{k \cdot s_1 - z_1}{r} \pmod N$.
- **Flamingo Polynomial Nonce Bias (`check_flamingo_polynomial_bias`)**:
  Scans signatures for structured shell nonces ($k = \text{SCALE} \cdot (10n^2 + 2)$) across transactions.
- **Key Backdoor Offset Audit (`check_key_backdoor_offset`)**:
  Verifies if a private key matches a backdoored constant offset $d \equiv N - 384 \cdot C \pmod N$.
- **UTXO & Script Hazard Scanning (`scan_utxo_script`)**:
  Detects dust traps ($< 546$ sats), OP_RETURN unspendable traps, CLTV/CSV timelocks, and non-standard multi-sig script traps.
- **Mempool Front-Running Risk Assessor (`assess_frontrun_risk`)**:
  Calculates exposure risks and anti-frontrun priority fee rates ($3.5\times$ to $5.0\times$ mempool rate) to protect transactions from automated mempool front-running bots.

### 2. `DeminingRig` (Execution & Sweeper Engine)
- **`audit_address`**: Conducts a full security audit across an address's signatures and UTXOs.
- **`build_safe_sweep_payload`**: Generates a high-priority, anti-frontrunning sweep transaction payload for recovered keys.
- **`batch_demine_file`**: Processes CSV/JSON datasets of signatures or UTXOs and exports structured JSON security reports.

---

## II. CLI USAGE EXAMPLES

### 1. Self-Contained Demonstration
Runs a complete test harness demonstrating nonce mine recovery, script trap detection, and safe anti-frontrun payload generation:
```bash
python3 demining_tools.py --demo
```

### 2. Demining an Address
Audits an address for signature and UTXO hazards:
```bash
python3 demining_tools.py --scan-address 1HSFck3ePBRaF81wBBDrMNggPstMWFvjUv
```

### 3. Batch Demining a Dataset
Processes a CSV file containing `address,txid,r,s,z` records:
```bash
python3 demining_tools.py --demine-file deep_scan_simulation.csv --output demining_report.json
```

---

## III. UNIT TESTING

Run the comprehensive unit test suite:
```bash
pytest test_demining_tools.py
```
