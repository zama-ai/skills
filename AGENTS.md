# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, etc.) when working with code in this repository.

## Project

**zama-protocol** — a Claude Code plugin containing three skills for AI agents building confidential smart contracts with Zama's FHEVM.

- **Install:** `/plugin marketplace add zama-ai/skills && /plugin install zama-protocol@zama-skills`
- **License:** BSD-3-Clause-Clear

## Skills

| Skill | When to use |
|-------|-------------|
| `zama-protocol` | FHE concepts, protocol architecture, planning, verified addresses, universal gotchas |
| `zama-solidity` | Writing/reviewing encrypted Solidity — FHE types, ACL, ERC-7984, Foundry/Hardhat setup |
| `zama-typescript` | TypeScript SDK integration — React, browser, Node.js, MV3, sessions, token flows |

## Structure

```
skills-repo/                         ← this repo (zama-ai/skills)
├── .claude-plugin/
│   ├── marketplace.json             # Marketplace index (single plugin, source: "./")
│   └── plugin.json                  # Plugin manifest (name: zama-protocol)
├── skills/
│   ├── zama-protocol/
│   │   ├── SKILL.md                 # Protocol concepts, universal gotchas, cross-references
│   │   └── references/
│   │       ├── concepts.md          # FHEVM mental model, planning, production readiness
│   │       └── addresses.md         # Verified contract addresses
│   ├── zama-solidity/
│   │   ├── SKILL.md                 # Solidity router + domain-specific reminders
│   │   └── references/
│   │       └── solidity/
│   │           ├── solidity.md      # Encrypted Solidity router + config
│   │           ├── erc7984.md       # Confidential token recipe + interface
│   │           ├── fhe-advanced.md  # Raw FHE ops, manual ACL, production decryption
│   │           └── setups/
│   │               ├── foundry.md
│   │               └── hardhat.md
│   └── zama-typescript/
│       ├── SKILL.md                 # TypeScript router + domain-specific reminders
│       └── references/
│           └── typescript/
│               ├── typescript.md    # SDK mental model + environment matrix
│               ├── sdk-package-and-signers.md
│               ├── sdk-token-flows.md
│               ├── sdk-custom-contract-flows.md
│               ├── sdk-permissions-and-sessions.md
│               ├── react-sdk.md
│               └── setups/
│                   ├── react-wagmi.md
│                   ├── browser-viem.md
│                   ├── browser-ethers.md
│                   ├── node-backend.md
│                   ├── extension-mv3.md
│                   └── local-hardhat.md
├── AGENTS.md                        # this file (CLAUDE.md is a symlink here)
├── CLAUDE.md                        # symlink → AGENTS.md
└── README.md
```

## Key Rules

**Say "FHEVM"** — uppercase. Not "fhEVM" or "FheVM." Zama convention.

**Skills teach corrections, not tutorials.** Every line must either fill a verified LLM blind spot or teach an essential concept. If a stock LLM already gets it right AND humans don't need it explained, cut it.

**Link to living code, don't embed it.** Code in a skill file can't be tested or linted and goes stale. Point to:
- [OpenZeppelin Confidential Contracts](https://github.com/OpenZeppelin/openzeppelin-confidential-contracts) — ERC-7984, token patterns
- [zama-ai/dapps](https://github.com/zama-ai/dapps/tree/main/packages/hardhat/contracts) — example contracts
- [zama-ai/protocol-apps](https://github.com/zama-ai/protocol-apps/tree/main/contracts) — deployed contracts

**Use ERC-7984** for any confidential token work. Never reimplement encrypted balances, allowances, or transfers.

**No duplication across skills.** Universal gotchas live in zama-protocol. Domain skills carry only domain-specific reminders and cross-reference zama-protocol for the full set.

## Editing

1. Edit the relevant `skills/<name>/SKILL.md` or files under `skills/<name>/references/`.
2. Bump the version in `.claude-plugin/marketplace.json` — that's the single source of truth.

### Before adding content

1. Check official docs: https://docs.zama.ai
2. Verify the API against the latest packages.
3. Test with a stock LLM — does it actually get this wrong?
4. If the LLM already knows it AND humans don't need it explained, don't add it.

## References

- **Zama Docs:** https://docs.zama.ai
- **Protocol addresses:** https://docs.zama.org/protocol/protocol-apps/addresses
- **FHEVM Solidity:** https://github.com/zama-ai/fhevm
- **SDK:** https://github.com/zama-ai/sdk
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
