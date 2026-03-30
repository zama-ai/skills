# Handoff — Where We Left Off

## What This Project Is

**fheskills** is an external-facing skill set for AI agents building encrypted smart contracts with Zama's FHEVM. It's modeled directly after [ethskills](https://github.com/austintgriffith/ethskills) — same structure, same "What You Probably Got Wrong" framing, same blind-spot-correction methodology.

**ethskills** = general Ethereum development knowledge for AI agents.
**fheskills** = FHE-specific knowledge for AI agents building with Zama's encrypted computation.

## What's Done

The repo is scaffolded at `/Users/aurora/Desktop/aurora/ai-skills/fheskills/` with git initialized (no commits yet). All 12 skills are written:

| Skill | Status | Notes |
|-------|--------|-------|
| `SKILL.md` (root router) | Done | Routes to all skills, "What to Fetch by Task" table |
| `ship/SKILL.md` | Done | Entry point, archetype templates, phase-by-phase routing |
| `concepts/SKILL.md` | Done | "Nothing is plaintext", FHE.select, ACL mental model, trivial vs real encryption |
| `fhevm/SKILL.md` | Done | Full API reference — types, operations, casting, random, inputs |
| `acl/SKILL.md` | Done | The #1 bug source — allowThis/allow patterns, delegation, checklist |
| `patterns/SKILL.md` | Done | Confidential ERC-20 (full impl), encrypted voting, sealed-bid auction |
| `testing/SKILL.md` | Done | Hardhat + FHEVM plugin, createEncryptedInput, decrypt helpers |
| `security/SKILL.md` | Done | 7 FHE-specific vulns + standard Solidity checklist |
| `addresses/SKILL.md` | Done | **Verified from official sources** — core infra, 7 confidential wrappers, ZAMA token across 6 chains, staking, governance, pausing |
| `tools/SKILL.md` | Done | Hardhat setup, packages, workflow, deployment script |
| `frontend/SKILL.md` | Done | fhevmjs, encryption flow, decryption states, button states |
| `deployment/SKILL.md` | Done | ZamaEthereumConfig, Sepolia-first workflow, verification |
| `migration/SKILL.md` | Done | Step-by-step process for adding FHE to existing contracts |

**Config files done:** `.claude-plugin/plugin.json`, `vercel.json`, `.gitignore`, `index.html`
**Symlinks done:** `CLAUDE.md`, `AGENTS.md`, `llms.txt` all point to `SKILL.md`

## Address Sources

Addresses were pulled from two official sources:
- **Core infra (ACL, Coprocessor, KMSVerifier):** `ZamaConfig.sol` in `github.com/zama-ai/fhevm/library-solidity/config/`
- **Protocol addresses (tokens, wrappers, staking, governance):** `github.com/zama-ai/protocol-apps/tree/main/docs/addresses`

## What's NOT Done

1. **No commits yet** — files are staged but not committed
2. **No remote repo** — needs `gh repo create` or manual GitHub setup
3. **Blind-spot triage not run** — the ethskills methodology says to spawn a fresh LLM, ask it to build something with FHEVM, and document every mistake. Content was seeded from the existing `fhevm-developer` skill in zama-marketplace + official docs, but hasn't been validated against actual LLM failure modes
4. **No CONTRIBUTING.md** — should document the triage methodology
5. **Technical content not fully verified** — the API patterns (FHE.sol functions, fhevmjs client-side API) were taken from the existing internal skill. Should be cross-checked against the latest `@fhevm/solidity` npm package and Zama docs at https://docs.zama.ai/protocol
6. **No audit skill** — ethskills has a deep `audit/SKILL.md` with parallel sub-agents across 19 domains. fheskills could benefit from an FHE-specific audit skill
7. **Domain not set up** — needs fheskills.com (or similar) + Vercel deployment
8. **The user was looking at ethskills' `audit/SKILL.md`** in the IDE — they may want to create an FHE-specific audit skill next

## Key Design Decisions

- **euint64 as default** (not euint256) — matches Zama's convention, cheaper gas
- **Hardhat only** (not Foundry) — FHEVM doesn't have Foundry support
- **BSD-3-Clause-Clear license** — matches Zama's licensing
- **"FHEVM" capitalization** — lowercase "fh", uppercase "EVM" per Zama convention
- **Silent failure pattern** — transfers that fail due to insufficient balance transfer 0 instead of reverting (privacy-preserving)
