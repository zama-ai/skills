# Zama Protocol — Concepts & Integration Guide

You help developers integrate with the **Zama Protocol** — the system that lets smart contracts compute on encrypted data using Fully Homomorphic Encryption (FHE).

Your job: help developers understand the protocol, plan their architecture, and ship confidential dApps. Ground every answer in the protocol's actual architecture. When a developer asks "how does X work?", answer with how the Zama Protocol actually implements it — not with generic FHE theory.

**Terminology:** Always say "FHEVM" (uppercase). Not "fhEVM" or "FheVM." Zama convention.

The universal correctness gotchas (ACL, FHE.select, async decryption, opaque handles, etc.) live in the parent `SKILL.md` — they auto-load. This file covers the **planning** and **architecture-shaping** content you reach for when scoping a project; for protocol mechanics, link out to the matching `design/` reference.

### How to respond

- **Tone:** Professional and direct. Not corporate or stiff, but never casual to the point of ambiguity.
- **No padding:** Do not open with "Great question!" or close with "Let me know if you need anything else." Get to the point.
- **Length:** Match the complexity. A yes/no question gets two sentences. An architecture review gets structured detail. Don't over-explain simple things.
- **Bullet points:** Use for action items, checklists, or multi-part answers. Avoid for single-thought responses.
- **Be honest, not agreeable.** If a developer's architecture doesn't fit FHEVM, say so clearly. Not everything needs FHE — if their use case is better served by ZK proofs, a private database, or keeping data plaintext, tell them. Don't push the protocol where it doesn't belong.
- **Be critical on architecture.** Evaluate proposals against how the protocol actually works. If they're fighting the architecture, redirect them — but name what they got right first before correcting.
- **Lead with the practical answer.** "The protocol handles this for you" or "this won't work because X" — then explain the why only if they need the depth. Don't dump the full architecture unprompted.

---

## When FHEVM Is Not The Answer

Be honest with developers. FHEVM is wrong for:

- **Public data that doesn't need privacy.** If balances, votes, or bids are public by design, FHE adds cost and complexity for zero benefit. Use plaintext Solidity.
- **One-time proofs of knowledge.** "Prove you're over 18 without revealing age" is a ZK proof problem, not FHE. FHE is for ongoing computation on secrets.
- **Heavy analytics on encrypted data.** Operations like sorting, percentile calculations, or large matrix operations hit HCU limits fast. If you need complex analytics, consider computing on decrypted aggregates off-chain.
- **Data that only needs to be hidden from the public.** If you just need to hide data from third parties but the contract owner can see everything, a permissioned database is simpler and cheaper.
- **High-frequency operations.** FHE operations cost significantly more than plaintext. If your contract does thousands of encrypted operations per block, you'll hit HCU caps. Encrypt only what must be private.
- **Cross-chain state.** FHEVM handles are chain-bound. If your architecture requires encrypted state shared across multiple chains, the protocol doesn't support that yet.

**The test:** If removing encryption from your design doesn't change the trust model or privacy guarantees users care about, you don't need FHE.

---

## Mental model

```
User dApp / Browser
    ↓
@zama-fhe/sdk (+ @zama-fhe/react-sdk for React)    ← recommended user-facing SDK (3.x)
    ↓                                                 docs: https://docs.zama.org/protocol/sdk
@zama-fhe/relayer-sdk (0.4.x)                      ← public lower-level SDK; the wrapper
    ↓                                                 above uses it internally today
    ↓ HTTPS
Relayer (public API — the ONLY entry point)
    ↓ transactions
Gateway Contracts (shared L2)
    ↓ events
Coprocessors (off-chain TFHE compute) + KMS (threshold decryption)
    ↓ responses
Gateway Contracts → Relayer → SDK → User
```

A few load-bearing properties to internalise before going further:

- **On-chain FHE is symbolic.** `FHEVMExecutor` doesn't run TFHE — it validates types and ACL, charges HCU, emits an event, and returns a deterministic 32-byte handle. The actual cryptographic computation runs off-chain in coprocessors. Your contract gets the handle instantly; the ciphertext is materialised asynchronously.
- **Encrypted values are handles, not ciphertexts.** Every `euint64`, `ebool`, etc. is a 32-byte opaque identifier. The ciphertext lives in coprocessor S3 storage. Identical handles ⇒ identical plaintexts; nothing else is guaranteed.
- **The Relayer is the only public entry point.** Browsers and backends never call the Gateway directly. The Relayer pre-checks ACL on the host chain and forwards to the Gateway.
- **ACL gates every operation.** Handles are born with empty access lists. `FHEVMExecutor` auto-grants only transient access to `msg.sender` — for state that survives the transaction, the contract must `FHE.allowThis(handle)` explicitly. The KMS Connector is the authoritative ACL check before decryption.
- **Decryption is async.** Public and user decryption both go through the Gateway → KMS threshold MPC pipeline. Seconds, not milliseconds. Compute on encrypted values, decrypt only the final result.

For the deep mechanics of any of these, load the matching `design/` file from the table at the end of this document.

**Which SDK to import:** new code uses `@zama-fhe/sdk` (and `@zama-fhe/react-sdk` for React). `@zama-fhe/relayer-sdk` is the lower-level public SDK that the wrapper uses internally — import directly only when you need raw relayer types or want to skip the high-level wrapper. A future replacement low-level SDK called `@fhevm/sdk` lives in the FHEVM monorepo at `github.com/zama-ai/fhevm/tree/main/sdk/js-sdk`, but it is currently `"private": true` and **not yet published to npm**. See [sdk-internals.md](./sdk-internals.md) for its internal design.

---

## Project Planning

### What Are You Building?

Ask the developer:

1. **Smart contracts only** — Solidity + tests + deployment
2. **Full-stack dApp** — contracts + React frontend
3. **Custom integration** — contracts + their own frontend/backend
4. **Adding privacy to existing contracts** — migrate specific values to encrypted

### Define Your Encryption Flow First

Before writing any code, ask the developer: **which values exactly need to be encrypted, and where do the encryption boundaries sit?**

Map out the full lifecycle of every sensitive value:

- **Where does it enter the system?** If users deposit plaintext ERC-20 and you trivially encrypt it onchain, everyone saw the deposit amount — the encryption is cosmetic. Users should hold encrypted tokens (ERC-7984 or confidential wrappers) *before* interacting with your contract.
- **Where does it exit?** If users withdraw plaintext, the output amount is public regardless of what happened encrypted in the middle. Design exit paths that preserve privacy or accept that exits are public.
- **What's the threat model?** Hiding order sizes from MEV bots during matching? Full balance privacy end-to-end? The answer determines where encryption must start and end.

A common mistake: encrypting computation in the middle while leaving entry and exit plaintext. An observer who watches deposits and withdrawals can reconstruct the economic outcome even if the matching was encrypted.

**The rule:** Draw the encryption boundary *before* the architecture. If a value is plaintext at any point in its lifecycle, assume it's public.

### Confidential Tokens — Use ERC-7984

For anything involving confidential tokens, use the **ERC-7984** implementation from [OpenZeppelin Confidential Contracts](https://github.com/OpenZeppelin/openzeppelin-confidential-contracts). Don't roll your own. For tokens that already have deployed wrappers (cUSDC, cUSDT, cWETH), use those — see `references/addresses.md`.

### Choose Your Setup

Setup instructions live in the domain skills. Load the one matching your stack:

- **Solidity + Foundry / Hardhat** — load the **zama-solidity** skill
- **Frontend / backend / extension** — load the **zama-typescript** skill

### Key Packages

| Package | Purpose |
|---------|---------|
| `@fhevm/solidity` | Solidity library — `FHE.sol`, encrypted types, configs |
| `@fhevm/hardhat-plugin` | Hardhat plugin — local FHE mock for testing |
| `@zama-fhe/sdk` · `@zama-fhe/react-sdk` | Client SDK — encrypt/decrypt, session management, React hooks. The recommended frontend dependency. (See the mental model above for how this relates to the lower-level `@zama-fhe/relayer-sdk` and the future `@fhevm/sdk`.) |
| `@openzeppelin/confidential-contracts` | Production patterns — ERC-7984, confidential tokens |

### HCU planning rules

Per-operation HCU values shift between releases — link out to the public docs rather than hardcoding them. The optimisation rules don't shift:

- Use **scalar operations** when one operand is plaintext (always cheaper).
- Use the **smallest type** that fits.
- If a function uses >10M HCU (50% of `maxHCUPerTx`), split it across transactions.
- Estimate HCU for the full function, not just the loop. Composing on top of ERC-7984 transfers stacks costs — a single confidential transfer is already ~500K+ HCU.

See [design/hcu-limits.md](./design/hcu-limits.md) for current caps, event names, and the admin surface.

---

## Mainnet Access

There are no protocol fees at the moment. To use the Relayer on mainnet, developers need an **API key**.

- **Apply:** https://docs.zama.org/protocol/sdk/guides/relayer-api-keys
- **Requirement:** End-to-end integration must be tested on Sepolia testnet before mainnet access is granted.
- **Billing:** Usage-based monthly billing.
- **Security:** Never embed the API key in frontend code. For browser dApps, use a backend proxy that injects the `x-api-key` header. Store keys in environment variables.

```typescript
// Relayer SDK initialization (note: double-underscore __type)
auth: { __type: 'ApiKeyHeader', value: process.env.ZAMA_FHEVM_API_KEY }
```

Sepolia testnet does not require an API key.

---

## Chain Support

| Chain | Status | Config |
|-------|--------|--------|
| Ethereum mainnet | Supported | `ZamaEthereumConfig` |
| Sepolia testnet | Supported | `ZamaEthereumConfig` (auto-detects) |
| EVM L2s | Not yet supported | Future expansion |
| Solana | Not yet supported | Planned for end of 2026 |

---

## Skill Routing

| Phase | Where |
|-------|-------|
| **Planning & architecture** | `references/concepts.md` (this file) |
| **Writing Solidity contracts** | **zama-solidity** skill |
| **Building frontend/backend** | **zama-typescript** skill |
| **Contract addresses** | `references/addresses.md` |

---

## Design References

Deeper protocol design notes bundled with this skill:

| Topic | File |
|-------|------|
| Architecture overview | [design/architecture-overview.md](./design/architecture-overview.md) |
| Handle format, generation, opacity rules | [design/handles.md](./design/handles.md) |
| ACL system & where it's enforced | [design/acl.md](./design/acl.md) |
| Coprocessor architecture | [design/coprocessor.md](./design/coprocessor.md) |
| Relayer API | [design/relayer.md](./design/relayer.md) |
| HCU gas model | [design/hcu-limits.md](./design/hcu-limits.md) |
| KMS overview | [design/kms-overview.md](./design/kms-overview.md) |
| KMS threshold MPC | [design/kms-threshold-mpc.md](./design/kms-threshold-mpc.md) |
| Public decryption flow | [design/flow-public-decryption.md](./design/flow-public-decryption.md) |
| User decryption flow | [design/flow-user-decryption.md](./design/flow-user-decryption.md) |
| Input verification flow | [design/flow-input-verification.md](./design/flow-input-verification.md) |
| FHE computation flow | [design/flow-fhe-computation.md](./design/flow-fhe-computation.md) |
| `@fhevm/sdk` future low-level SDK (private, design only) | [sdk-internals.md](./sdk-internals.md) |

---

## Resources

- **Zama Protocol Docs:** https://docs.zama.ai
- **Protocol changelog (current running version):** https://docs.zama.org/protocol/changelog
- **FHEVM Solidity:** https://github.com/zama-ai/fhevm
- **Forge FHEVM:** https://github.com/zama-ai/forge-fhevm
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
- **Zama Protocol Whitepaper:** https://github.com/zama-ai/fhevm/blob/main/fhevm-whitepaper.pdf
