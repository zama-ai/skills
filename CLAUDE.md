# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

**fheskills** is the external-facing skill set for AI agents building encrypted smart contracts with Zama's FHEVM.

**Deployed at:** https://fheskills.com
**License:** BSD-3-Clause-Clear

## Structure

```
fheskills/
├── SKILL.md                    # Router — links to all skills
├── AGENTS.md                   # Agent discovery
├── skills/
│   ├── general/SKILL.md        # Protocol architecture, planning, integration guide
│   ├── solidity/SKILL.md       # Encrypted contract development reference
│   ├── solidity/setup/SKILL.md # Foundry + Hardhat project scaffolding
│   ├── typescript/SKILL.md     # Frontend/backend SDK integration
│   └── addresses/SKILL.md      # Verified contract addresses
├── .claude-plugin/plugin.json  # Claude plugin metadata
├── index.html                  # Landing page
└── vercel.json                 # Deployment config
```

## Key Rules

**Say "FHEVM"** — uppercase. Not "fhEVM" or "FheVM." Zama convention.

**Skills teach corrections, not tutorials.** Every line must either fill a verified LLM blind spot or teach essential concepts. If stock LLMs already know it AND humans don't need it explained, cut it.

**Link to living code, don't embed it.** Code in a skill file can't be tested, can't be linted, and goes stale silently. Point to:
- [OpenZeppelin Confidential Contracts](https://github.com/OpenZeppelin/openzeppelin-confidential-contracts) — ERC-7984, token patterns
- [zama-ai/dapps](https://github.com/zama-ai/dapps/tree/main/packages/hardhat/contracts) — example contracts
- [zama-ai/protocol-apps](https://github.com/zama-ai/protocol-apps/tree/main/contracts) — deployed contracts

**Use ERC-7984** for any confidential token work. Don't roll your own.

## Editing Skills

1. Edit skills in `skills/<skill>/SKILL.md`
2. Test locally: `python3 -m http.server 8000`
3. Verify at `http://localhost:8000`

### Before adding content

1. Check official docs: https://docs.zama.ai
2. Verify API against latest `@fhevm/solidity` package
3. Test with a stock LLM — does it actually get this wrong?
4. If the LLM already knows it, don't add it

## Starting Templates

**Foundry:**
```bash
git clone https://github.com/zama-ai/fhevm-foundry-template
```

**Hardhat:**
```bash
git clone https://github.com/zama-ai/fhevm-hardhat-template
```

**Frontend:**
```bash
git clone https://github.com/zama-ai/fhevm-react-template
```

## Deployment

Static markdown files deployed via Vercel. No build step. Automatic on push to main.

## References

- **Zama Docs:** https://docs.zama.ai
- **Tech Specs:** https://github.com/zama-ai/tech-spec/tree/new-tech-specs
- **FHEVM Solidity:** https://github.com/zama-ai/fhevm
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
