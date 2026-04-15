# Zama Protocol

The missing knowledge between AI agents and production encrypted smart contracts on Zama's FHEVM.

**Entry point:** [`SKILL.md`](SKILL.md) — start here. It covers the non-negotiable FHEVM gotchas and routes you to the right reference.

## References

All loaded on demand from [`references/`](references/), nested by domain:

```
references/
├── concepts.md                 — FHEVM mental model, planning, production readiness
├── addresses.md                — verified contract addresses (never guess)
├── solidity/
│   ├── solidity.md             — encrypted Solidity router (types, ACL, HCU, config)
│   ├── erc7984.md              — confidential token recipe + interface
│   ├── fhe-advanced.md         — raw FHE ops, manual ACL, production decryption
│   └── setups/
│       ├── foundry.md          — default
│       └── hardhat.md
└── typescript/
    ├── typescript.md           — SDK mental model + environment matrix
    └── setups/
        ├── react-wagmi.md      — default
        ├── browser-viem.md
        ├── browser-ethers.md
        ├── node-backend.md
        ├── extension-mv3.md
        └── local-hardhat.md
```

## Install

```
/plugin marketplace add zama-ai/skills
/plugin install zama-protocol@zama-skills
```

See the [repo root README](../../README.md) for alternatives (manual clone, git submodule).
