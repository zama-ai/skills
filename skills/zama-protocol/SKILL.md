---
name: zama-protocol
description: Zama Protocol concepts, architecture, and planning for FHEVM (Fully Homomorphic Encryption on Ethereum). Use when the user asks about FHE concepts, protocol architecture, how the coprocessor/relayer/gateway/KMS works, ACL semantics, handle format, HCU limits, decryption flows, the low-level `@fhevm/sdk` design, whether FHE fits their use case, planning a confidential dApp, or needs verified FHEVM contract addresses. Also load this skill first whenever the user mentions FHEVM, Zama, or encrypted onchain computation — it carries the universal gotchas that apply to both Solidity and TypeScript work. For writing Solidity contracts, load the zama-solidity skill. For TypeScript SDK integration and the `@zama-fhe/sdk` wrapper, load the zama-typescript skill.
license: BSD-3-Clause-Clear
---

# Zama Protocol — FHEVM Concepts & Architecture

You are probably wrong about FHE on Ethereum. How the coprocessor works, what happens onchain vs off-chain, ACL semantics, decryption flow — stock training data is missing or stale. This skill fills those gaps.

**Say "FHEVM"** (uppercase). Not "fhEVM" or "FheVM". Zama convention.

---

## How to use these skills

This skill covers protocol-level concepts and the universal gotchas. Two companion skills handle implementation:

| Need | Skill |
|------|-------|
| Protocol architecture, planning, deciding if FHE fits | **This skill** — read `references/concepts.md` |
| Deep protocol design (handles, ACL, coprocessor, KMS, decryption flows, the low-level SDK) | **This skill** — files under `references/design/` (indexed at the bottom of `concepts.md`) |
| Verified contract addresses (never guess) | **This skill** — read `references/addresses.md` |
| Writing or reviewing encrypted Solidity contracts | **zama-solidity** |
| TypeScript SDK integration (React/viem/ethers/Node) | **zama-typescript** |

Load references on demand — don't read them all up front.

## Universal gotchas (every FHEVM task)

These are the LLM blind spots that ship as bugs in stock-model output. Keep them in mind regardless of which companion skill you load next. Deeper explanations are in `references/concepts.md` (the "What You Probably Got Wrong" section).

1. **ACL is mandatory and easy to miss.** Every encrypted value is born with an empty ACL. `FHEVMExecutor` auto-grants only **transient** access to `msg.sender` — never `tx.origin`, never persistent. For state that survives the transaction the contract must call `FHE.allowThis(handle)`, and `FHE.allow(handle, user)` for any user who needs to decrypt. Miss either and the code compiles and deploys cleanly, but the **next** transaction that uses the stored handle reverts with `ACLNotAllowed(handle, msg.sender)`. The bug doesn't show at deploy time — it shows the second time someone interacts with the contract.
2. **No branching on encrypted values.** `if (FHE.gt(a, b))` does not compile. Use `FHE.select(cond, ifTrue, ifFalse)` — both branches always execute, which is what makes it private.
3. **Decryption is async and last.** Production decryption goes through the Relayer → Gateway → KMS threshold MPC pipeline — seconds, not milliseconds. Compute entirely on encrypted values, decrypt only the final result.
4. **Handles are opaque.** The only protocol guarantee is "identical handles ⇒ identical plaintexts." Do not compare, hash, or key off handle values. The same op in two different blocks now produces different handles (`blockhash` + `block.timestamp` are in the preimage).
5. **`euint64` is the default for balances, not `euint256`.** Larger types cost dramatically more HCU per op. Use the smallest type that fits.
6. **FHE ops are not `view` and cost HCU.** They are state-changing coprocessor calls.
7. **Trivial encryption is not private.** `FHE.asEuintN(constant)` is visible onchain — constants and defaults only. Real privacy comes from user-encrypted inputs via the SDK.
8. **`FHE.div` and `FHE.rem` take a plaintext divisor only.** Redesign any formula with encrypted state in the denominator.
9. **`fheRandBounded` requires a power of 2.** `FHE.randEuint8(100)` reverts. Use `FHE.randEuint8(128)`.
10. **Input ciphertexts bind to one target contract.** Cross-contract hops require re-encryption; wrong target produces a runtime ACL revert.
11. **Never emit encrypted handles in events.** Handle changes leak mutation timing and identity. Emit plaintext metadata only.
12. **Use ERC-7984 for confidential tokens.** Don't reimplement encrypted balances, allowances, or transfers. `@openzeppelin/confidential-contracts` has the audited implementation.
13. **Config: inherit `ZamaEthereumConfig` first.** It sets the correct coprocessor addresses per `block.chainid` for mainnet, Sepolia, and local Hardhat.

## Canonical sources

- **Zama Docs:** https://docs.zama.ai
- **Protocol changelog (authoritative — current running version):** https://docs.zama.org/protocol/changelog
- **Protocol addresses:** https://docs.zama.org/protocol/protocol-apps/addresses
- **FHEVM Solidity library:** https://github.com/zama-ai/fhevm
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
- **HCU cost tables:** https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md
- **Example dApps:** https://github.com/zama-ai/dapps/tree/main/packages/hardhat/contracts
