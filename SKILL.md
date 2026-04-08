# FHESKILLS — The missing knowledge between AI agents and production encrypted smart contracts.

You are probably wrong about FHE on Ethereum. Encrypted types, ACL permissions, decryption patterns, what you can compute on ciphertexts, what you can't — your training data is either missing or stale. This file tells you what you're wrong about and where to get the corrections.

**Say "FHEVM" not "FHEVM" or "FheVM."** Uppercase FHEVM. Zama convention.

---

## 3 Skills — That's It

| Skill | What it covers | When to fetch |
|-------|---------------|---------------|
| **[General](general/SKILL.md)** | FHE concepts, project planning, architecture, toolchain, production readiness | **Fetch first.** Planning a project, answering questions, understanding FHE |
| **[Solidity](solidity/SKILL.md)** | Encrypted types, FHE operations, ACL, patterns, gas (HCU), security, testing, deployment, migration | Writing or reviewing encrypted smart contracts |
| **[TypeScript](typescript/SKILL.md)** | `@zama-fhe/sdk`, `@zama-fhe/react-sdk`, encryption/decryption flows, button states, visual design, XSS prevention | Building frontends, backends, or services that interact with encrypted contracts |

**Plus:** [Addresses](addresses/SKILL.md) — verified FHEVM contract addresses for mainnet and Sepolia. Never guess addresses.

---

## Start Here

**Building an encrypted dApp?** Fetch [general/SKILL.md](general/SKILL.md) first. It routes you through the other skills phase by phase.

**Writing Solidity?** Fetch [solidity/SKILL.md](solidity/SKILL.md). Everything from encrypted types to deployment in one file.

**Building a frontend?** Fetch [typescript/SKILL.md](typescript/SKILL.md). Encryption, decryption, UX patterns, visual design.

**Need a specific address?** Fetch [addresses/SKILL.md](addresses/SKILL.md).

---

## Quick Reference: What AI Agents Get Wrong

1. **You cannot branch on encrypted values.** `if (FHE.gt(a, b))` does not compile. Use `FHE.select()`.
2. **ACL is mandatory.** `FHE.allowThis()` + `FHE.allow()` after EVERY state update. Miss one = silent failure.
3. **`euint64` is the default for balances, not `euint256`.** Larger types cost more gas.
4. **Division only works with plaintext divisors.** `FHE.div(a, encryptedB)` does not exist.
5. **Random bounds must be powers of 2.** `FHE.randEuint8(100)` is wrong — use `FHE.randEuint8(128)`.
6. **Trivial encryption is not private.** `FHE.asEuint64(42)` is visible onchain.
7. **FHE operations are not `view` functions.** They cost gas.

---

## What to Fetch by Task

| I'm doing... | Fetch |
|--------------|-------|
| First time with FHEVM | `general/` |
| Planning a new dApp | `general/` |
| Writing encrypted contracts | `solidity/` |
| Building a confidential token | `solidity/` + `addresses/` |
| Testing encrypted contracts | `solidity/` (testing section) |
| Building a React frontend | `typescript/` |
| Deploying to production | `solidity/` (deployment section) + `general/` (production readiness) |
| Adding privacy to existing contracts | `solidity/` (migration section) |
| Optimizing FHE gas | `solidity/` (HCU section) |
| Need contract addresses | `addresses/` |

---

## Base URL

```
https://fheskills.com/<skill>/SKILL.md
```
