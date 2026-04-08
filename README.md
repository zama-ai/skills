# FHESKILLS

The missing knowledge between AI agents and production encrypted smart contracts.

Built on [Zama's FHEVM](https://docs.zama.ai/protocol) — Fully Homomorphic Encryption on EVM-compatible blockchains.

## What is this?

A skill set that teaches AI agents (and developers) how to build confidential dApps with FHEVM. Each skill is a standalone markdown file that fills verified LLM blind spots — things stock models get wrong about encrypted smart contracts.

## 3 Skills — That's It

| Skill | What it covers |
|-------|---------------|
| **[General](general/SKILL.md)** | FHE concepts, project planning, architecture, toolchain, production readiness |
| **[Solidity](solidity/SKILL.md)** | Encrypted types, FHE operations, ACL, patterns, gas (HCU), security, testing, deployment, migration |
| **[TypeScript](typescript/SKILL.md)** | `@zama-fhe/sdk`, `@zama-fhe/react-sdk`, encryption/decryption, button states, visual design, XSS prevention |

**Plus:** [Addresses](addresses/SKILL.md) — verified FHEVM contract addresses for mainnet and Sepolia.

## Quick Start

Fetch the entry point:

```
https://fheskills.com/general/SKILL.md
```

It routes you through all other skills phase by phase.

## What AI Agents Get Wrong About FHE

1. **You cannot branch on encrypted values.** `if (FHE.gt(a, b))` does not compile. Use `FHE.select()`.
2. **ACL is mandatory.** Every encrypted value needs `FHE.allowThis()` + `FHE.allow()` after storage. Miss one and the value silently becomes unusable.
3. **`euint64` is the default for balances, not `euint256`.** Larger types cost more gas for every operation.
4. **Division only works with plaintext divisors.** `FHE.div(a, encryptedB)` does not exist.
5. **Random bounds must be powers of 2.** `FHE.randEuint8(100)` is wrong — use `FHE.randEuint8(128)`.
6. **Trivial encryption is not secure.** `FHE.asEuint64(42)` is visible onchain. Only `FHE.fromExternal()` with user-submitted inputs is truly private.
7. **FHE operations are not `view` functions.** They cost gas. Every encrypted add, multiply, or compare is state-changing.

## Content Methodology

Every line is classified:

- **Red** — Verified LLM blind spot (stock models get this wrong)
- **Purple** — Essential human teaching material
- **Yellow** — LLM knows but skips in practice
- **Green** — Already known, doesn't need teaching

Only red and purple lines survive.

## Getting Started as a Developer

### Smart Contract Template

```bash
git clone https://github.com/zama-ai/fhevm-hardhat-template
cd fhevm-hardhat-template
npm install
```

### Frontend Template

```bash
git clone https://github.com/zama-ai/fhevm-react-template
cd fhevm-react-template
npm install
```

### OpenZeppelin Confidential Contracts

```bash
npm install @openzeppelin/confidential-contracts
```

Repository: [OpenZeppelin/openzeppelin-confidential-contracts](https://github.com/OpenZeppelin/openzeppelin-confidential-contracts)

## URL Pattern

```
https://fheskills.com/<skill>/SKILL.md
```

## License

BSD-3-Clause-Clear
