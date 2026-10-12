# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, etc.) when working with code in this repository.

## Project

A Claude Code plugin (id: `zama-protocol`, marketplace: `zama-skills`) bundling three skills for AI agents building confidential smart contracts with Zama's FHEVM. Note: the plugin id happens to match one of the bundled skill names — context disambiguates.

- **Install:** `/plugin marketplace add zama-ai/skills && /plugin install zama-protocol@zama-skills`
- **License:** BSD-3-Clause-Clear

## Skills

| Skill | When to use |
|-------|-------------|
| `zama-protocol` | The FHEVM model shared by contracts and clients, package choice, planning, deployed addresses |
| `zama-solidity` | Writing/reviewing encrypted Solidity — contract rules with examples, ERC-7984, reveals, deployed apps, Hardhat/Foundry |
| `zama-typescript` | Clients with `@zama-fhe/sdk` — version-matched docs and examples, rules that hold across releases |

## Structure

```
.claude-plugin/                  # Plugin metadata; version source
skills/
  zama-protocol/                # Shared model, packages, planning, protocol registry
  zama-solidity/                # Contract rules, ERC-7984, reveals, deployed apps, setup
  zama-typescript/              # SDK discovery, official examples, client rules
.cursor/rules/                  # Generated; removed references remove their rules
.codex-plugin/                  # Generated
.agents/plugins/                # Generated marketplace
scripts/                        # Artifact generators
tests/                          # Generator regression checks
```

## Key Rules

**Say "FHEVM"** — uppercase. Not "fhEVM" or "FheVM." Zama convention.

**Skills teach corrections, not tutorials.** Every line must either fill a verified LLM blind spot or teach an essential concept. If a stock LLM already gets it right AND humans don't need it explained, cut it.

**Write for a first read.** One rule per heading, in plain words, with the reason in a sentence. Agents load SKILL.md on every task; put everything else in a reference the SKILL.md routes to.

**Link to maintained sources; embed no contract or client code.** Embedded code goes stale, and agents copy fragments without the checks around them. Point to:
- [OpenZeppelin Confidential Contracts](https://github.com/OpenZeppelin/openzeppelin-confidential-contracts) — ERC-7984, token patterns
- [Protocol registry](https://github.com/zama-ai/protocol-registry) — deployed addresses
- The SDK's version-tagged `llms.txt` and official `examples/` — client code
- The [Zama code examples](https://docs.zama.org/protocol/examples) — complete contracts with tests
- The Solidity code map — Etherscan-verified mainnet application sources

State each rule in prose with exact identifiers, and link the complete example that shows it.

**Use ERC-7984** for any confidential token work. Never reimplement encrypted balances, allowances, or transfers.

**Publish only public, verifiable content.** No private code, private links, internal discussions or people's names. Every statement must be supported by public docs, published packages or verified on-chain source. Application code pointers lead to Etherscan-verified mainnet source, including current proxy implementations.

**No duplication across skills.** zama-protocol holds the model shared by contracts and clients. zama-solidity holds contract rules; zama-typescript holds client rules. Both load zama-protocol first.

## Editing

1. Edit the relevant `skills/<name>/SKILL.md` or files under `skills/<name>/references/`.
2. Bump the version in `.claude-plugin/marketplace.json` — that's the single source of truth.

### Before adding content

1. Check official docs: https://docs.zama.org
2. Verify the API against the published packages.
3. For new advice, test with a stock LLM — does it actually get this wrong?
4. If the LLM already knows it AND humans don't need it explained, don't add it.

## References

- **Zama Docs:** https://docs.zama.org
- **Protocol addresses:** https://github.com/zama-ai/protocol-registry
- **FHEVM Solidity:** https://github.com/zama-ai/fhevm
- **SDK:** https://github.com/zama-ai/sdk
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
