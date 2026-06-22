# Zama Skills

The missing knowledge between AI agents and production encrypted smart contracts.

Built on [Zama's FHEVM](https://docs.zama.ai/protocol) — Fully Homomorphic Encryption on EVM-compatible blockchains.

## What is this?

A plugin (id: `zama-protocol`, in the `zama-skills` marketplace) bundling three skills that teach AI agents how to build confidential dApps with FHEVM. Fills the gaps where stock models get encrypted smart contracts wrong.

| Skill               | What it covers                                                                       |
| ------------------- | ------------------------------------------------------------------------------------ |
| **zama-protocol**   | FHE concepts, protocol architecture, planning, verified addresses, universal gotchas |
| **zama-solidity**   | Encrypted Solidity — FHE types, ACL, ERC-7984, Foundry/Hardhat setup                 |
| **zama-typescript** | TypeScript SDK — React, browser, Node.js, MV3, token flows, sessions                 |

All three install together and route automatically by context — protocol questions load `zama-protocol`, Solidity work loads `zama-solidity`, TypeScript/SDK work loads `zama-typescript`.

## Install

### Claude Code

```bash
/plugin marketplace add zama-ai/skills
/plugin install zama-protocol@zama-skills
```

Update later with `/plugin marketplace update zama-skills`.

### Any AI agent (via `npx skills`)

```bash
npx skills add zama-ai/skills
```

Add `--list` to pick which skills to install: `npx skills add zama-ai/skills --list`.

Prefer a global install under `~/.agents` over per-project. Update later with `npx skills update`.

### Codex

```bash
codex plugin marketplace add zama-ai/skills
# then open /plugins in Codex and pick the Zama plugin
```

Codex reads `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json` from the repo. Update later with `codex plugin marketplace upgrade zama-skills`.

### Cursor

Cursor rules live under `.cursor/rules/` — one `.mdc` per skill plus one per reference (e.g. `zama-protocol-zama-solidity--erc7984.mdc`). Two options:

```bash
# Option A — clone into your project and point Cursor at the rules:
git clone https://github.com/zama-ai/skills.git ~/src/zama-skills
ln -s ~/src/zama-skills/.cursor/rules/* /path/to/your-project/.cursor/rules/

# Option B — copy the rules into your project:
cp -r ~/src/zama-skills/.cursor/rules/. /path/to/your-project/.cursor/rules/
```

### Manual clone + symlink

Works with any agent that reads global skills from `~/.agents/skills/`:

```bash
git clone https://github.com/zama-ai/skills.git ~/src/zama-skills
mkdir -p ~/.agents/skills
ln -s ~/src/zama-skills/skills/zama-protocol   ~/.agents/skills/zama-protocol
ln -s ~/src/zama-skills/skills/zama-solidity   ~/.agents/skills/zama-solidity
ln -s ~/src/zama-skills/skills/zama-typescript ~/.agents/skills/zama-typescript
```

### Replacing a previous install

If you installed an earlier version through a different marketplace, remove it first:

```bash
/plugin marketplace remove zama-skills   # Claude Code
```

## License

BSD-3-Clause-Clear
