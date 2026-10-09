# Zama Skills

The missing knowledge between AI agents and production encrypted smart contracts.

Built on [Zama's FHEVM](https://docs.zama.org/protocol) — Fully Homomorphic Encryption on EVM-compatible blockchains.

## What is this?

A plugin (id: `zama-protocol`, in the `zama-skills` marketplace) bundling three skills that teach AI agents how to build confidential dApps with FHEVM. Fills the gaps where stock models get encrypted smart contracts wrong.

| Skill               | What it covers                                                                       |
| ------------------- | ------------------------------------------------------------------------------------ |
| **zama-protocol**   | The FHEVM model, package choice, planning, deployed addresses                        |
| **zama-solidity**   | Encrypted Solidity — contract rules with examples, ERC-7984, reveals, Hardhat/Foundry |
| **zama-typescript** | Clients with `@zama-fhe/sdk` — React, viem, ethers, Node, official examples           |

All three install together. Their descriptions route protocol questions to `zama-protocol`, contract work to `zama-solidity`, and client work to `zama-typescript`. Contract and client skills load `zama-protocol` first, and references are read only when a task needs them. The skills point to maintained sources — the protocol registry, OpenZeppelin, the SDK's version-matched docs and examples, and verified mainnet contracts — rather than copying tutorials.

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

Cursor rules live under `.cursor/rules/`: one `.mdc` per skill plus one per reference (e.g. `zama-protocol-zama-solidity--erc7984.mdc`). Clone the repository once, then generate the rules into your project. Run the same commands to update:

```bash
git clone https://github.com/zama-ai/skills.git ~/src/zama-skills   # first time only
git -C ~/src/zama-skills pull --ff-only
uv run ~/src/zama-skills/scripts/translate_for_cursor.py --output /path/to/your-project/.cursor/rules
```

The generator replaces symlinked rules with files, removes rules it generated earlier that no longer exist and links left dangling, and leaves every other file in the directory alone.

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

Update the existing installation through the same channel. When migrating from copied folders or another plugin, retire the old installation before enabling the replacement: same-name skills are not a merged source of truth. Keep backups outside skill-discovery directories.

## License

BSD-3-Clause-Clear
