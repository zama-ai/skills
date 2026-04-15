# zama-ai/skills

Claude Code skills published by Zama. Each subdirectory is a standalone skill with its own `SKILL.md`, references, and plugin manifest. The repo root carries the marketplace index.

## Skills

| Skill | What it does |
|-------|--------------|
| [`fheskill`](./fheskill) | Build confidential smart contracts and dApps on Zama's FHEVM — FHE concepts, Solidity patterns (encrypted types, ACL, HCU, ERC-7984), TypeScript SDK integration, verified addresses. |

## Install

### Claude Code plugin marketplace

Add this repo as a marketplace once, then install any skill from it:

```
/plugin marketplace add zama-ai/skills
/plugin install fheskill@zama-skills
```

To update later:

```
/plugin marketplace update zama-skills
```

### Manual install

Clone the repo and symlink the skill into your Claude skills directory:

```bash
git clone https://github.com/zama-ai/skills.git ~/src/zama-skills
ln -s ~/src/zama-skills/fheskill ~/.claude/skills/fheskill
```

Or copy into a project's local skills folder:

```bash
cp -r ~/src/zama-skills/fheskill ./.claude/skills/fheskill
```

### Fetch on demand (no install)

Agents that support URL fetch can pull the router directly — no install step, always the latest:

```
https://fheskills.com/SKILL.md
```

Per-task references are linked from the router and are fetched as needed under `https://fheskills.com/references/...`.

## Layout

```
skills/                              ← this repo
├── .claude-plugin/
│   └── marketplace.json             ← marketplace index
├── README.md                        ← you are here
└── fheskill/                        ← the skill
    ├── SKILL.md                     ← always-loaded router
    ├── .claude-plugin/plugin.json
    ├── references/                  ← on-demand reference files
    │   ├── concepts.md
    │   ├── addresses.md
    │   ├── solidity/
    │   └── typescript/
    ├── AGENTS.md
    ├── CLAUDE.md
    ├── README.md
    ├── index.html
    └── vercel.json
```

Future skills live as sibling subdirectories — `./fheskill`, `./other-skill`, etc. — and get added to `marketplace.json`.

## License

BSD-3-Clause-Clear
