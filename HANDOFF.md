# Handoff — Where We Left Off

## What This Project Is

**fheskills** is an external-facing skill set for AI agents building encrypted smart contracts with Zama's FHEVM. It's modeled directly after [ethskills](https://github.com/austintgriffith/ethskills) — same structure, same "What You Probably Got Wrong" framing, same blind-spot-correction methodology.

**ethskills** = general Ethereum development knowledge for AI agents.
**fheskills** = FHE-specific knowledge for AI agents building with Zama's encrypted computation.

## What's Done

The repo is at `/Users/aurora/Desktop/aurora/ai-skills/fheskills/` with 2 commits on main. **22 skills total** — 12 FHE-specific + 10 adapted from ethskills:

### FHE-Specific Skills (Written or Adapted for FHE)

| Skill | Status | Notes |
|-------|--------|-------|
| `SKILL.md` (root router) | Done | Routes to all 22 skills, "What to Fetch by Task" table |
| `ship/SKILL.md` | Done | Entry point, archetype templates, phase-by-phase routing |
| `concepts/SKILL.md` | Done | Ethskills concepts — "Nothing is automatic", incentive design |
| `fhevm/SKILL.md` | Done | Full API reference — types, operations, casting, random, inputs |
| `acl/SKILL.md` | Done | The #1 bug source — allowThis/allow patterns, delegation, checklist |
| `patterns/SKILL.md` | Done | Confidential ERC-20 (full impl), encrypted voting, sealed-bid auction |
| `testing/SKILL.md` | Done | Hardhat + FHEVM plugin + ethskills testing philosophy merged |
| `security/SKILL.md` | Done | 7 FHE vulns + full ethskills Solidity security merged |
| `addresses/SKILL.md` | Done | **Verified from official sources** — core infra, 7 wrappers, ZAMA token across 6 chains |
| `tools/SKILL.md` | Done | Hardhat setup, packages, workflow |
| `frontend/SKILL.md` | Done | fhevmjs, encryption flow, decryption states |
| `frontend-ux/SKILL.md` | Done | 3 decryption types, 6-state buttons, signature caching, XSS prevention |
| `deployment/SKILL.md` | Done | ZamaEthereumConfig, Sepolia-first workflow |
| `migration/SKILL.md` | Done | Step-by-step adding FHE to existing contracts |
| `gas/SKILL.md` | Done | Full HCU cost tables from official docs, optimization patterns |
| `building-blocks/SKILL.md` | Done | Confidential DeFi — ERC-7984, wrap/unwrap boundary, vault/swap/lending patterns |
| `production-ready/SKILL.md` | Done | 5 contract reqs, 4 frontend reqs, templates, pre-prod checklist |

### Ethskills Skills (Included As-Is)

| Skill | Notes |
|-------|-------|
| `standards/SKILL.md` | ERC-20, ERC-721, ERC-7984, ERC-4337, ERC-8004 |
| `l2s/SKILL.md` | L2 landscape, chain selection |
| `wallets/SKILL.md` | EOAs, smart wallets, multisig, AA |
| `indexing/SKILL.md` | Events, The Graph |
| `audit/SKILL.md` | 500+ item security audit across 19 domains |
| `frontend-playbook/SKILL.md` | IPFS, Vercel, ENS deployment |

**Config files:** `.claude-plugin/plugin.json`, `vercel.json`, `.gitignore`, `index.html`
**Symlinks:** `CLAUDE.md`, `AGENTS.md`, `llms.txt` → `SKILL.md`

## Address Sources

- **Core infra (ACL, Coprocessor, KMSVerifier):** `ZamaConfig.sol` in `github.com/zama-ai/fhevm/library-solidity/config/`
- **Protocol addresses:** `github.com/zama-ai/protocol-apps/tree/main/docs/addresses`
- **HCU costs:** `github.com/zama-ai/fhevm/docs/solidity-guides/hcu.md`

## What's NOT Done

1. **Uncommitted changes** — TODO work (gas, building-blocks, security, testing, frontend-ux, production-ready) needs to be committed
2. **No remote repo** — needs `gh repo create` or manual GitHub setup
3. **Blind-spot triage not run** — content hasn't been validated against actual LLM failure modes
4. **No CONTRIBUTING.md**
5. **Technical content not fully verified** — API patterns should be cross-checked against latest `@fhevm/solidity`
6. **Domain not set up** — needs fheskills.com + Vercel deployment
7. **`frontend/SKILL.md` overlaps with `frontend-ux/SKILL.md`** — consider merging or differentiating (frontend = technical API, frontend-ux = UX patterns)
8. **Ethskills skills not adapted for FHE** — standards, l2s, wallets, indexing, audit, frontend-playbook are included as-is from ethskills. Could add FHE-specific context to each.
9. **`index.html` not updated** — doesn't include the new skills (gas, building-blocks, frontend-ux, production-ready)

## Key Design Decisions

- **euint64 as default** (not euint256) — matches Zama's convention, cheaper gas
- **Hardhat only** (not Foundry) — FHEVM doesn't have Foundry support
- **BSD-3-Clause-Clear license** — matches Zama's licensing
- **"FHEVM" capitalization** — uppercase FHEVM per Zama convention
- **Silent failure pattern** — transfers that fail due to insufficient balance transfer 0 instead of reverting (privacy-preserving)
- **Three decryption types** — public decrypt ("reveal public value"), user decrypt ("decrypt"), delegate decrypt ("decrypt on behalf of user")
- **HCU limits** — 20M global, 5M depth per transaction
