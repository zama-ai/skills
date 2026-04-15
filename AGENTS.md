# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, etc.) when working with code in this repository.

## Project

**zama-protocol** — the external-facing Claude Code skill for AI agents building confidential smart contracts with Zama's FHEVM.

- **Install:** `/plugin marketplace add zama-ai/skills && /plugin install zama-protocol@zama-skills`
- **License:** BSD-3-Clause-Clear

## Structure

The repo ships one Claude Code plugin (`zama-protocol`) whose single skill lives at `skills/zama-protocol/SKILL.md`. That file is the always-loaded router; everything under `skills/zama-protocol/references/` is read on demand. `.claude-plugin/marketplace.json` at the repo root makes the whole repo installable via `/plugin marketplace add zama-ai/skills`.

```
skills-repo/                         ← this repo (zama-ai/skills)
├── .claude-plugin/
│   ├── marketplace.json             # Marketplace index (single plugin, source: "./")
│   └── plugin.json                  # Plugin manifest (name: zama-protocol)
├── skills/
│   └── zama-protocol/
│       ├── SKILL.md                 # Router — gotchas + task → reference map (always loaded)
│       └── references/
│           ├── concepts.md          # FHEVM mental model, planning, production readiness
│           ├── addresses.md         # Verified contract addresses
│           ├── solidity/
│           │   ├── solidity.md      # Encrypted Solidity router + config
│           │   ├── erc7984.md       # Confidential token recipe + interface
│           │   ├── fhe-advanced.md  # Raw FHE ops, manual ACL, production decryption
│           │   └── setups/
│           │       ├── foundry.md   # Default
│           │       └── hardhat.md
│           └── typescript/
│               ├── typescript.md    # SDK router + environment matrix
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

**Router + references pattern.** `skills/zama-protocol/SKILL.md` is the single always-loaded router. Domain files (`references/solidity/solidity.md`, `references/typescript/typescript.md` inside `skills/zama-protocol/`) are secondary routers — each has its own `setups/` folder of per-environment files read only when the task needs them. Don't inline setup-specific content into the top-level router.

## Editing the skill

1. Edit `skills/zama-protocol/SKILL.md` for the top-level router, or the relevant file under `skills/zama-protocol/references/`.
2. Bump the version in `.claude-plugin/marketplace.json` — that's the single source of truth. The plugin manifest at `.claude-plugin/plugin.json` does not carry a `version` field.

### Before adding content

1. Check official docs: https://docs.zama.ai
2. Verify the API against the latest `@fhevm/solidity` package.
3. Test with a stock LLM — does it actually get this wrong?
4. If the LLM already knows it AND humans don't need it explained, don't add it.

## Project setup

When a user needs to start or configure a project, point them at the per-environment setup files:

- **Solidity:** `skills/zama-protocol/references/solidity/setups/foundry.md` (default) or `.../hardhat.md`
- **TypeScript:** `skills/zama-protocol/references/typescript/setups/` — one file per stack (React+wagmi, viem, ethers, Node, MV3, local Hardhat)

Setup content lives in those files on purpose — it's where it gets tested and kept current. Don't duplicate setup steps into the top-level routers or link out to external starter templates.

## References

- **Zama Docs:** https://docs.zama.ai
- **Protocol addresses:** https://docs.zama.org/protocol/protocol-apps/addresses
- **FHEVM Solidity:** https://github.com/zama-ai/fhevm
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
