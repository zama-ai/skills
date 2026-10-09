# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, etc.) when working with code in this repository.

## Project

A Claude Code plugin (id: `zama-protocol`, marketplace: `zama-skills`) bundling three skills for AI agents building confidential smart contracts with Zama's FHEVM. Note: the plugin id happens to match one of the bundled skill names — context disambiguates.

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
.claude-plugin/                  # Plugin metadata; version source
skills/
  zama-protocol/                # Universal rules, concepts, deployment discovery
  zama-solidity/                # Contract decisions, verified code map, setup pointers
  zama-typescript/              # SDK router and integration pitfalls
.cursor/rules/                  # Generated; removed references remove their rules
.codex-plugin/                  # Generated
.agents/plugins/                # Generated marketplace
scripts/                        # Artifact generators
tests/                         # Generator regression checks
```


## Key Rules

**Say "FHEVM"** — uppercase. Not "fhEVM" or "FheVM." Zama convention.

**Skills teach corrections, not tutorials.** Every line must either fill a verified LLM blind spot or teach an essential concept. If a stock LLM already gets it right AND humans don't need it explained, cut it.

**Link to living code, don't embed it.** Code in a skill file can't be tested or linted and goes stale. Point to:
- [OpenZeppelin Confidential Contracts](https://github.com/OpenZeppelin/openzeppelin-confidential-contracts) — ERC-7984, token patterns
- The Solidity code map — Etherscan-verified Ethereum mainnet application sources

**Use ERC-7984** for any confidential token work. Never reimplement encrypted balances, allowances, or transfers.

**Never publish private code or links.** Private apps may inform investigation, but distributed advice must be independently supported by public APIs/docs. Application code pointers must lead to verified mainnet Etherscan source, including current proxy implementations.

**No duplication across skills.** Universal gotchas live in zama-protocol. Domain skills carry only domain-specific reminders and cross-reference zama-protocol for the full set.

## Editing

1. Edit the relevant `skills/<name>/SKILL.md` or files under `skills/<name>/references/`.
2. Bump the version in `.claude-plugin/marketplace.json` — that's the single source of truth.

### Before adding content

1. Check official docs: https://docs.zama.org
2. Verify the API against the latest packages.
3. For new advice, test with a stock LLM — does it actually get this wrong?
4. If the LLM already knows it AND humans don't need it explained, don't add it.

## References

- **Zama Docs:** https://docs.zama.org
- **Protocol addresses:** https://docs.zama.org/protocol/protocol-apps/addresses
- **FHEVM Solidity:** https://github.com/zama-ai/fhevm
- **SDK:** https://github.com/zama-ai/sdk
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
