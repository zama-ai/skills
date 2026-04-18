---
name: zama-solidity
description: Write confidential Solidity smart contracts on Zama's FHEVM. Use when the user is writing, reviewing, or debugging encrypted Solidity — FHE types (euint64, ebool), ACL (FHE.allowThis/allow), FHE.select, ERC-7984 confidential tokens, ZamaEthereumConfig, `@fhevm/solidity`, `@openzeppelin/confidential-contracts`, Foundry or Hardhat setup for FHEVM, or any Solidity code that uses the FHE library. For protocol concepts and architecture, load the zama-protocol skill. For TypeScript SDK integration, load the zama-typescript skill.
---

# Zama Solidity — Confidential Smart Contracts

Encrypted Solidity on FHEVM. This skill covers contract patterns, FHE operations, ACL, ERC-7984 tokens, and project setup.

**Before writing any code:** load the **zama-protocol** skill and read the universal gotchas — they cover the protocol-level bugs that apply to all FHEVM work (branching on encrypted values, ACL semantics, trivial encryption, HCU costs, decryption flow). What follows here is Solidity-specific.

---

## References

Load on demand — don't read them all up front.

| Task | Read |
|------|------|
| Config, encrypted types, FHE gotchas for contracts | `references/solidity/solidity.md` |
| Confidential token (encrypted ERC-20, hidden balances) | `references/solidity/erc7984.md` |
| Hand-written FHE ops, manual ACL, production decryption | `references/solidity/fhe-advanced.md` |
| Foundry project setup | `references/solidity/setups/foundry.md` *(default)* |
| Hardhat project setup | `references/solidity/setups/hardhat.md` |
| Verified contract addresses | `references/addresses.md` — **never guess addresses** |

---

## Solidity-specific reminders

These supplement the universal gotchas in the zama-protocol skill.

- **Inherit `ZamaEthereumConfig` first.** It sets the correct coprocessor addresses per `block.chainid`. Without it, FHE calls silently fail.

- **Use ERC-7984 for any confidential token.** Never reimplement encrypted balances, allowances, or transfers. `@openzeppelin/confidential-contracts` has the audited implementation. See `references/solidity/erc7984.md`.

- **ACL after every state update.** `FHE.allowThis(handle)` for the contract, `FHE.allow(handle, user)` for decrypt access. ERC-7984 handles this internally; only hand-written FHE code needs it. For single-tx cross-contract handles, prefer `FHE.allowTransient` over persistent `FHE.allow`.

- **`FHE.select` branches must be encrypted values.** Both arms must be the same encrypted type — materialise zeros with `FHE.asEuint64(0)`, not a literal `0`. Both branches always execute.

- **Silent failures on insufficient balance.** FHE contracts transfer 0 via `FHE.select` — no revert. Test the zero-transfer case and call every function twice to prove ACL persistence.

- **Foundry needs `via_ir = true`; Hardhat does not.**

- **`FHE.makePubliclyDecryptable(handle)` after every update** to a publicly-decryptable state variable.

- **Decryption helpers are test-only.** `decrypt`, `userDecrypt`, etc. don't exist on production `FHE.sol`. Make decryption the last step — no conditional actions after.

## Canonical sources

- **FHEVM Solidity library:** https://github.com/zama-ai/fhevm
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
- **HCU cost tables:** https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md
- **Example contracts:** https://github.com/zama-ai/dapps/tree/main/packages/hardhat/contracts
