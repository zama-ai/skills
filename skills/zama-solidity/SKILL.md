---
name: zama-solidity
description: Write, review, or debug confidential Solidity on Zama FHEVM — FHE types/operations, ACL, ERC-7984, @fhevm/solidity, @openzeppelin/confidential-contracts, or Foundry/Hardhat setup. Also use for HCU cost/depth, ciphertext dependencies, escrow, auctions, RFQ, and batchers. Load zama-protocol first; use zama-typescript for SDK integration.
license: BSD-3-Clause-Clear
---

# Zama Solidity

Load **zama-protocol** first for universal correctness/privacy rules. Keep this skill focused on contract decisions; read only the matching reference.

| Task | Read |
|------|------|
| Design, HCU/dependencies, deployed patterns | `references/code-map.md` |
| Confidential tokens, wrappers, escrow | `references/erc7984.md` |
| Raw FHE operations, ACL, public settlement | `references/fhe-advanced.md` |
| Foundry / Hardhat setup | `references/setups/foundry.md` / `references/setups/hardhat.md` |
| Deployment/configuration | **zama-protocol** → `references/addresses.md` |

## Contract review priorities

- **Use OpenZeppelin ERC-7984 for token accounting.** Review the actual value movement in vault/escrow/payment code: encrypted assertions about an amount are not custody of tokens. Prefer the official deployed wrapper when it fits the application's requirements.
- **Account for the transferred result.** Insufficient balance or receiver rejection can produce an encrypted zero transfer. Never credit the requested amount without validating what actually moved.
- **Keep correctness through optimisation.** Preserve overflow bounds, rounding, refunds, cancellation and settlement stages. Client-computed deposits remain untrusted; reduced HCU alone is not a validated speedup.
- **Store results with persistent ACL access.** Pass temporary cross-contract values with transient grants. Test subsequent transactions, zero-transfer paths and caller permissions on existing handles.
- **Use production decryption proofs.** Local decrypt helpers are test-only. Freeze expected public-result handles, verify the ordered proof and prevent duplicate economic actions.

For supported overloads, consult the installed `FHE.sol` and [FHEVM API reference](https://docs.zama.org/protocol/solidity-guides/smart-contract/functions.md). Respect library/tooling peer dependencies and template pins; the newest package combination is not necessarily compatible.
