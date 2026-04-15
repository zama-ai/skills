# zama-ai/skills

Claude Code skills published by Zama. Each skill lives under [`plugins/`](./plugins) with its own `SKILL.md` and references. The repo root carries the marketplace index.

## Install

Inside any Claude Code session, run these two commands:

```
/plugin marketplace add zama-ai/skills
/plugin install zama-protocol@zama-skills
```

That's it. The `zama-protocol` plugin is now installed and will trigger automatically when you mention FHEVM, confidential contracts, ERC-7984, or the Zama SDK. To pull updates later, run `/plugin marketplace update zama-skills`.

## Skills

| Skill | What it does |
|-------|--------------|
| [`zama-protocol`](./plugins/zama-protocol) | Build confidential smart contracts and dApps on Zama's FHEVM — FHE concepts, Solidity patterns (encrypted types, ACL, HCU, ERC-7984), TypeScript SDK integration, verified addresses. |

## Other install methods

<details>
<summary><b>Manual clone + symlink</b> — no plugin system required</summary>

```bash
git clone https://github.com/zama-ai/skills.git ~/src/zama-skills
ln -s ~/src/zama-skills/plugins/zama-protocol ~/.claude/skills/zama-protocol
```

Or copy into a project's local skills folder:

```bash
cp -r ~/src/zama-skills/plugins/zama-protocol ./.claude/skills/zama-protocol
```
</details>

## Layout

```
skills/                                 ← this repo
├── .claude-plugin/
│   └── marketplace.json                ← marketplace index (pluginRoot: "./plugins")
├── README.md                           ← you are here
└── plugins/
    └── zama-protocol/                   ← the skill
        ├── SKILL.md                     ← always-loaded router
        ├── .claude-plugin/plugin.json
        ├── references/                  ← on-demand reference files
        │   ├── concepts.md
        │   ├── addresses.md
        │   ├── solidity/
        │   └── typescript/
        ├── AGENTS.md
        ├── CLAUDE.md
        └── README.md
```

Future skills live as sibling subdirectories under `plugins/` (e.g. `plugins/zama-protocol`, `plugins/other-skill`, …) and get added to `marketplace.json`.

## License

BSD-3-Clause-Clear
