# 🦩 Project Flamingo: Sovereign Recovery Guide

This document outlines the procedure for recovering Bitcoin assets once a private key has been mathematically derived using the RK-AMOS engine.

## I. PREREQUISITES
1.  **RK-AMOS Convergence:** Ensure the solver has successfully recovered the 256-bit scalar $d$ and verified it against the target public key.
2.  **Wallet Import Format (WIF):** The scalar must be converted to WIF for import. The `crypto_utils.py` module provides `to_wif()` for this purpose.
3.  **Secure Environment:** All recovery actions must be performed on an offline, air-gapped machine or a trusted hardware-accelerated node.

## II. SWEEPING PROTOCOL
To move funds from a recovered address to a secure cold-storage destination, follow these steps:

1.  **WIF Preparation:**
    - Use `to_wif(d, compressed=True)` to generate the WIF string.
2.  **Import to Electrum:**
    - Open Electrum.
    - Go to **Wallet** -> **Private Keys** -> **Sweep**.
    - Enter the derived WIF.
3.  **Transaction Construction:**
    - Set the destination address to a trusted cold-storage address.
    - **Fee Selection:** Use standard market rates for priority. Do not use excessively high fees unless required by mempool congestion. Verify the current mempool state at `mempool.space`.
4.  **Broadcast:**
    - Review the transaction details.
    - Sign and broadcast via a trusted node or public broadcast service.

## III. SECURITY WARNINGS
- **Never share private keys or WIFs.**
- **Verify target addresses double-blind.**
- **Be aware of potential front-running on unconfirmed transactions.**

---
**Status:** Operational
**Goal:** Integrity and Sovereignty.
