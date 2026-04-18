---
name: zama-protocol
description: Zama Protocol concepts, architecture, and planning for FHEVM (Fully Homomorphic Encryption on Ethereum). Use when the user asks about FHE concepts, protocol architecture, how the coprocessor/relayer/gateway/KMS works, whether FHE fits their use case, planning a confidential dApp, or needs verified FHEVM contract addresses. Also load this skill first whenever the user mentions FHEVM, Zama, or encrypted onchain computation — it carries the universal gotchas that apply to both Solidity and TypeScript work. For writing Solidity contracts, load the zama-solidity skill. For TypeScript SDK integration, load the zama-typescript skill.
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
| Verified contract addresses (never guess) | **This skill** — read `references/addresses.md` |
| Writing or reviewing encrypted Solidity contracts | **zama-solidity** |
| TypeScript SDK integration (React/viem/ethers/Node) | **zama-typescript** |

Load references on demand — don't read them all up front.

---

## Non-negotiable gotchas (every FHEVM task)

These are the bugs stock models ship. Internalise them before writing any code — they apply to both Solidity contracts and TypeScript integrations.

1. **You cannot branch on encrypted values.** `if (FHE.gt(a, b))` does not compile. `FHE.gt` returns an `ebool` the EVM cannot evaluate. Use `FHE.select(cond, ifTrue, ifFalse)` — both branches always execute, which is what makes it private.

2. **ACL is mandatory — it is the #1 Zama bug.** Every encrypted value is born with an empty ACL. After creating or updating encrypted state, call `FHE.allowThis(handle)` so the contract can use it on the next call, and `FHE.allow(handle, user)` for any user who needs to decrypt. Miss one and the code compiles, deploys, and **silently** fails at runtime — no revert. `ERC7984` handles this internally; only hand-written FHE code needs manual ACL.

3. **Trivial encryption is not private.** `FHE.asEuint64(42)` is visible onchain — constants and defaults only. Real user privacy comes from `FHE.fromExternal(handle, proof)` (user-encrypted via the SDK with a ZKPoK).

4. **`euint64` is the default for balances, not `euint256`.** Larger types cost dramatically more HCU per op. Use the smallest type that fits your value range.

5. **FHE operations are not `view`.** They are state-changing coprocessor calls and cost gas (HCU — Homomorphic Compute Units).

6. **No encrypted divisor.** `FHE.div` and `FHE.rem` only accept a **plaintext** divisor. Redesign any formula with encrypted state in the denominator.

7. **Random bounds must be powers of 2.** `FHE.randEuint8(100)` is wrong. Use `FHE.randEuint8(128)`.

8. **Input ciphertexts bind to one target contract.** An encrypted input is tied to exactly the contract address passed at encryption time. Cross-contract hops need re-encryption. Wrong target → runtime ACL revert with no compile hint.

9. **Never emit encrypted values in events.** Handle changes leak mutation timing and identity. Emit addresses and plaintext metadata only.

10. **Info leaks through control flow.** Reverting on an encrypted condition reveals it. Same for conditional events, differing return values, or gas differences tied to encrypted state. If your contract behaves differently based on an encrypted value, you've leaked information.

11. **Decryption is async and last.** Production decryption goes through the Relayer → Gateway → KMS threshold MPC pipeline — seconds, not milliseconds. Compute entirely on encrypted values, decrypt only the final result, and perform no conditional actions after the decryption callback.

12. **Config: inherit `ZamaEthereumConfig` first.** It sets the correct coprocessor addresses (ACL, FHEVMExecutor, KMSVerifier) per `block.chainid` for mainnet, Sepolia, and local Hardhat.

13. **Use ERC-7984 for any confidential token.** Never reimplement encrypted balances, allowances, or transfers. `@openzeppelin/confidential-contracts` has the audited implementation.

## Canonical sources

- **Zama Docs:** https://docs.zama.ai
- **Protocol addresses:** https://docs.zama.org/protocol/protocol-apps/addresses
- **FHEVM Solidity library:** https://github.com/zama-ai/fhevm
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
- **HCU cost tables:** https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md
- **Example dApps:** https://github.com/zama-ai/dapps/tree/main/packages/hardhat/contracts
