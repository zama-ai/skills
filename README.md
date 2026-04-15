# zama-ai/skills

Claude Code skills published by Zama. Each subdirectory is a standalone skill with its own `SKILL.md` and references. The repo root carries the marketplace index.

## Install

Inside any Claude Code session, run these two commands:

```
/plugin marketplace add zama-ai/skills
/plugin install fheskill@zama-skills
```

That's it. The `fheskill` plugin is now installed and will trigger automatically when you mention FHEVM, confidential contracts, ERC-7984, or the Zama SDK. To pull updates later, run `/plugin marketplace update zama-skills`.

## Skills

| Skill | What it does |
|-------|--------------|
| [`fheskill`](./fheskill) | Build confidential smart contracts and dApps on Zama's FHEVM — FHE concepts, Solidity patterns (encrypted types, ACL, HCU, ERC-7984), TypeScript SDK integration, verified addresses. |

## Other install methods

<details>
<summary><b>Manual clone + symlink</b> — no plugin system required</summary>

```bash
git clone https://github.com/zama-ai/skills.git ~/src/zama-skills
ln -s ~/src/zama-skills/fheskill ~/.claude/skills/fheskill
```

Or copy into a project's local skills folder:

```bash
cp -r ~/src/zama-skills/fheskill ./.claude/skills/fheskill
```
</details>

<details>
<summary><b>Fetch on demand</b> — no install, always latest</summary>

Any agent or tool that supports HTTP fetch can pull the router directly:

```
https://fheskills.com/SKILL.md
```

Per-task references are linked from the router and fetched as needed under `https://fheskills.com/references/…`.
</details>

## Layout

```
skills/                              ← this repo
├── .claude-plugin/
│   └── marketplace.json             ← marketplace index
├── README.md                        ← you are here
├── vercel.json                      ← rewrites / → /fheskill for fheskills.com
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
    └── index.html
```

Future skills live as sibling subdirectories (`./fheskill`, `./other-skill`, …) and get added to `marketplace.json`.

## License

BSD-3-Clause-Clear
