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
| Deep protocol design (handles, ACL, coprocessor, KMS, flows, RFCs) | **This skill** — files under `references/design/` (see the Design References table at the bottom of `concepts.md`) |
| Verified contract addresses (never guess) | **This skill** — read `references/addresses.md` |
| Writing or reviewing encrypted Solidity contracts | **zama-solidity** |
| TypeScript SDK integration (React/viem/ethers/Node) | **zama-typescript** |

Load references on demand — don't read them all up front.

## Canonical sources

- **Zama Docs:** https://docs.zama.ai
- **Protocol changelog (authoritative — current running version):** https://docs.zama.org/protocol/changelog
- **Protocol addresses:** https://docs.zama.org/protocol/protocol-apps/addresses
- **FHEVM Solidity library:** https://github.com/zama-ai/fhevm
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
- **HCU cost tables:** https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md
- **Example dApps:** https://github.com/zama-ai/dapps/tree/main/packages/hardhat/contracts
