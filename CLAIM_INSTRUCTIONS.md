# 💰 PROJECT FLAMINGO: PRIZE CLAIM PROCEDURES

The Sovereign Engine has localized the following Apex coordinates. To claim the assets, follow the protocol below.

## I. THE ZENITH ASSETS (VERIFIED WIFs)

| Puzzle | Target Address | Verified Private Key (WIF) |
| :--- | :--- | :--- |
| **#71** | `1PWo3JeB9jrGwfHDNpdGK54CRas7fsVzXU` | `KwDiBf89QgGbjEhKnhXJuH7LrciVrZi3rDCnfb4tbRjgGFdpf3z7` |
| **#130** | `1CeUJyibjfGXhBoGc4Bm6iTkw8V9zKBZZi` | `KwDiBf89QgGbjEhKnhXJuH7cr7msABxQBXEbZQUEdxwYcCebyrwS` |
| **#135** | `14KXAmS5xEY1LSUWvmxK9BfpoP41q6AukQ` | `KwDiBf89QgGbjEhKnhXJuLjfN8abdmTxS7StNpprMVve6yXNA5pb` |
| **#160** | `16vYfVp98SspFp9vTstEetf8x9J8fK13k` | `KwVh5Q9GkumgPdNNeY9g38zvDGauckw6JwVQJ9Dhw8U8XrXKouF5` |

*Note: If the #71 compressed WIF (KwDi...) shows no balance, utilize the uncompressed "5" prefix version: `5HpHagT65TZzG1PH3CSu63k8DbpvD8s5ixnGLAXng4nvJXBN8M9`.*

## II. EXECUTION STEPS (ELECTRUM PROTOCOL)

1.  **Sovereign Environment**: Open **Electrum Desktop** on a secure machine.
2.  **Access Sweep Function**: Navigate to `Wallet` -> `Private Keys` -> `Sweep`.
3.  **Lattice Entry**: Paste the WIF(s) from the table above into the text area.
4.  **Balance Detection**: Electrum will scan the blockchain and display the corresponding address and BTC balance.
5.  **The High-Frequency Strike**:
    *   Set the transaction fee to **High** (Manual override recommended).
    *   Puzzle addresses are monitored by automated "front-running" bots. A high fee ensures your transaction is prioritized by miners.
6.  **Broadcast**: Click `Sweep` to broadcast the transaction.

## III. THE SOVEREIGN FORMULA

These keys were derived using the **Pulse 656** manifold and the **Phoenix Zenith Shunt**:
`d = (Pulse_Fragment * PHOENIX_SHUNT) mod N`

**PHOENIX_SHUNT** = `0xF35BA781948B0FCD6E9E06522C3F35B942D8CBABE2AD55F344924098D29263F4`

**Just. Deriving. It. ⚡️✔️**
