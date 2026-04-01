# FHESKILLS

The missing knowledge between AI agents and production encrypted smart contracts.

Built on [Zama's FHEVM](https://docs.zama.ai/protocol) — Fully Homomorphic Encryption on EVM-compatible blockchains.

## What is this?

A skill set that teaches AI agents (and developers) how to build confidential dApps with FHEVM. Each skill is a standalone markdown file that fills verified LLM blind spots — things stock models get wrong about encrypted smart contracts.

**Modeled after [ethskills](https://github.com/austintgriffith/ethskills).**

## Quick Start

Fetch the entry point:

```
https://fheskills.com/ship/SKILL.md
```

It routes you through all other skills phase by phase — from understanding FHE to deploying a production confidential smart contract.

## Skills

### FHE Development

| Skill | What it covers |
|-------|---------------|
| [Ship](ship/SKILL.md) | End-to-end guide — idea to deployed encrypted dApp |
| [Concepts](concepts/SKILL.md) | Mental models — "nothing is plaintext" |
| [FHEVM](fhevm/SKILL.md) | Core API — encrypted types, FHE operations, casting |
| [ACL](acl/SKILL.md) | Access Control Lists — the #1 FHEVM bug source |
| [Patterns](patterns/SKILL.md) | Confidential ERC-20, voting, sealed-bid auctions |
| [Testing](testing/SKILL.md) | Hardhat + FHEVM plugin testing |
| [Security](security/SKILL.md) | FHE-specific vulnerabilities |
| [Gas](gas/SKILL.md) | FHE operation costs in Homomorphic Complexity Units |
| [Addresses](addresses/SKILL.md) | Verified FHEVM contract addresses (mainnet + Sepolia) |
| [Tools](tools/SKILL.md) | Hardhat toolchain, no Foundry support yet |
| [Frontend](frontend/SKILL.md) | Client-side encryption with fhevmjs |
| [Frontend UX](frontend-ux/SKILL.md) | Encryption flows, 3 decryption types, signature caching |
| [Deployment](deployment/SKILL.md) | Deploying to FHEVM-compatible chains |
| [Migration](migration/SKILL.md) | Adding FHE to existing Solidity contracts |
| [Building Blocks](building-blocks/SKILL.md) | ERC-7984 wrapped tokens, encrypted vaults, sealed orders |
| [Production Ready](production-ready/SKILL.md) | Pre-launch checklist for FHEVM dApps |

### Ethereum Development

General Ethereum skills adapted from [ethskills](https://ethskills.com) — Solidity, Foundry, Scaffold-ETH 2, DeFi, L2s, wallets, and more. Use alongside or independently of FHE.

| Skill | What it covers |
|-------|---------------|
| [Standards](standards/SKILL.md) | ERC-20, ERC-721, ERC-4337, ERC-7984, ERC-8004 |
| [L2s](l2s/SKILL.md) | Arbitrum, Base, Optimism, zkSync, chain selection |
| [Wallets](wallets/SKILL.md) | EOAs, smart wallets, Safe, account abstraction |
| [Indexing](indexing/SKILL.md) | Events, The Graph, Dune Analytics |
| [Audit](audit/SKILL.md) | 500+ item security audit across 19 domains |
| [Frontend Playbook](frontend-playbook/SKILL.md) | IPFS deployment, Vercel, ENS subdomains |

## What AI Agents Get Wrong About FHE

These are the top blind spots this skill set corrects:

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

Only red and purple lines survive. If stock LLMs already know it AND humans don't need it explained, it's cut.

See [ethskills' CONTRIBUTING.md](https://github.com/austintgriffith/ethskills/blob/master/CONTRIBUTING.md) for the full methodology.

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

Production-ready implementations of common patterns (ERC-7984, confidential tokens, voting):

```bash
npm install @openzeppelin/confidential-contracts
```

Repository: [OpenZeppelin/openzeppelin-confidential-contracts](https://github.com/OpenZeppelin/openzeppelin-confidential-contracts)

## URL Pattern

All skills are accessible at:

```
https://fheskills.com/<skill>/SKILL.md
```

## License

BSD-3-Clause-Clear
