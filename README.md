# zama-protocol

The missing knowledge between AI agents and production encrypted smart contracts.

Built on [Zama's FHEVM](https://docs.zama.ai/protocol) — Fully Homomorphic Encryption on EVM-compatible blockchains.

## What is this?

A Claude Code plugin containing three skills that teach AI agents (and developers) how to build confidential dApps with FHEVM. Fills verified LLM blind spots — things stock models get wrong about encrypted smart contracts.

| Skill               | What it covers                                                                       |
| ------------------- | ------------------------------------------------------------------------------------ |
| **zama-protocol**   | FHE concepts, protocol architecture, planning, verified addresses, universal gotchas |
| **zama-solidity**   | Encrypted Solidity — FHE types, ACL, ERC-7984, Foundry/Hardhat setup                 |
| **zama-typescript** | TypeScript SDK — React, browser, Node.js, MV3, token flows, sessions                 |

## Install using npx skills (for any AI agent)

To install the skills for your favorite agent(s), run:

```
npx skills add git@github.com:zama-ai/skills.git
```

If this command fails, you can clone and install manually:

```
git clone git@github.com:zama-ai/skills.git /tmp/zama-skills
npx skills add /tmp/zama-skills --list
npx skills add /tmp/zama-skills
```

Select all Zama skills: `zama-protocol`, `zama-solidity`, `zama-typescript`. Prefer using a global installation in `~/.agents`.

If you have previously installed these skills in Claude through a marketplace, you can remove them by running in a Claude session:

```
/plugin marketplace remove zama-skills
```

To later update your installed skills:

```
npx skills update
```

## Install for Claude only

If you prefer installing the skills for Claude only (through a marketplace), run in a Claude session:

```
/plugin marketplace add zama-ai/skills
/plugin install zama-protocol@zama-skills
```

All three skills install together. They trigger automatically based on context — protocol questions load `zama-protocol`, Solidity work loads `zama-solidity`, TypeScript/SDK work loads `zama-typescript`.

To pull updates later, run `/plugin marketplace update zama-skills`.

<details>
<summary><b>Manual clone + symlink</b> — no plugin system required</summary>

```bash
git clone https://github.com/zama-ai/skills.git ~/src/zama-skills
# Symlink each skill you need:
mkdir -p ~/.agents/skills
ln -s ~/src/zama-skills/skills/zama-protocol ~/.agents/skills/zama-protocol
ln -s ~/src/zama-skills/skills/zama-solidity ~/.agents/skills/zama-solidity
ln -s ~/src/zama-skills/skills/zama-typescript ~/.agents/skills/zama-typescript
```

</details>

## What AI Agents Get Wrong About FHE

1. **You cannot branch on encrypted values.** `if (FHE.gt(a, b))` does not compile. Use `FHE.select()`.
2. **ACL is mandatory.** Every encrypted value needs `FHE.allowThis()` + `FHE.allow()` after storage. Miss one and the value silently becomes unusable.
3. **`euint64` is the default for balances, not `euint256`.** Larger types cost more gas for every operation.
4. **Division only works with plaintext divisors.** `FHE.div(a, encryptedB)` does not exist.
5. **Random bounds must be powers of 2.** `FHE.randEuint8(100)` is wrong — use `FHE.randEuint8(128)`.
6. **Trivial encryption is not secure.** `FHE.asEuint64(42)` is visible onchain. Only `FHE.fromExternal()` with user-submitted inputs is truly private.
7. **FHE operations are not `view` functions.** They cost gas. Every encrypted add, multiply, or compare is state-changing.

## Content Methodology

Every line is classified:

- **Red** — Verified LLM blind spot (stock models get this wrong)
- **Purple** — Essential human teaching material

Only red and purple lines survive.

## License

BSD-3-Clause-Clear
