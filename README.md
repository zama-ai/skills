# zama-protocol

The missing knowledge between AI agents and production encrypted smart contracts.

Built on [Zama's FHEVM](https://docs.zama.ai/protocol) — Fully Homomorphic Encryption on EVM-compatible blockchains.

## What is this?

A single Claude Code skill that teaches AI agents (and developers) how to build confidential dApps with FHEVM. Fills verified LLM blind spots — things stock models get wrong about encrypted smart contracts.

## Install

Inside any Claude Code session, run:

```
/plugin marketplace add zama-ai/skills
/plugin install zama-protocol@zama-skills
```

The skill triggers automatically when you mention FHE, FHEVM, confidential contracts, ERC-7984, or the Zama SDK. To pull updates later, run `/plugin marketplace update zama-skills`.

<details>
<summary><b>Manual clone + symlink</b> — no plugin system required</summary>

```bash
git clone https://github.com/zama-ai/skills.git ~/src/zama-skills
ln -s ~/src/zama-skills/skills/zama-protocol ~/.claude/skills/zama-protocol
```
</details>

## One Skill, Many References

Entry point: **[`skills/zama-protocol/SKILL.md`](skills/zama-protocol/SKILL.md)** — the router. It covers the non-negotiable FHEVM gotchas and points at the right reference file for the task at hand.

Reference files live under [`skills/zama-protocol/references/`](skills/zama-protocol/references/), nested by domain:

```
references/
├── concepts.md
├── addresses.md
├── solidity/
│   ├── solidity.md
│   ├── erc7984.md
│   ├── fhe-advanced.md
│   └── setups/{foundry,hardhat}.md
└── typescript/
    ├── typescript.md
    ├── sdk-package-and-signers.md
    ├── sdk-token-flows.md
    ├── sdk-custom-contract-flows.md
    ├── sdk-permissions-and-sessions.md
    ├── react-sdk.md
    └── setups/{react-wagmi,browser-viem,browser-ethers,node-backend,extension-mv3,local-hardhat}.md
```

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

## Getting started as a developer

Setup instructions live in the per-environment files so they stay testable and current. Task-specific SDK usage lives in the TypeScript reference files:

- **Solidity** — [`skills/zama-protocol/references/solidity/setups/foundry.md`](skills/zama-protocol/references/solidity/setups/foundry.md) (default) or [`skills/zama-protocol/references/solidity/setups/hardhat.md`](skills/zama-protocol/references/solidity/setups/hardhat.md)
- **TypeScript environments** — pick one file from [`skills/zama-protocol/references/typescript/setups/`](skills/zama-protocol/references/typescript/setups/) matching your stack (React+wagmi, viem, ethers, Node, MV3, local Hardhat)
- **TypeScript tasks** — use the focused files in [`skills/zama-protocol/references/typescript/`](skills/zama-protocol/references/typescript/) for token flows, custom-contract flows, permissions/sessions, React SDK patterns, and signer/migration guidance

For any confidential token work, use [OpenZeppelin Confidential Contracts](https://github.com/OpenZeppelin/openzeppelin-confidential-contracts) — never reimplement encrypted balances.

## License

BSD-3-Clause-Clear
