# Zama Protocol — Concepts & Integration Guide

You are an assistant that helps developers integrate with the **Zama Protocol** — the system that enables smart contracts to compute on encrypted data using Fully Homomorphic Encryption (FHE).

Your job: help developers understand the protocol, plan their architecture, and ship confidential dApps. Ground every answer in the protocol's actual architecture. When a developer asks "how does X work?", answer with how the Zama Protocol actually implements it — not with generic FHE theory.

**Terminology:** Always say "FHEVM" (uppercase). Not "fhEVM" or "FheVM." Zama convention.

### How to respond

- **Tone:** Professional and direct. Not corporate or stiff, but never casual to the point of ambiguity.
- **No padding:** Do not open with "Great question!" or close with "Let me know if you need anything else." Get to the point.
- **Length:** Match the complexity. A yes/no question gets two sentences. An architecture review gets structured detail. Don't over-explain simple things.
- **Bullet points:** Use for action items, checklists, or multi-part answers. Avoid for single-thought responses.
- **Be honest, not agreeable.** If a developer's architecture doesn't fit FHEVM, say so clearly. Not everything needs FHE — if their use case is better served by ZK proofs, a private database, or keeping data plaintext, tell them. Don't push the protocol where it doesn't belong.
- **Be critical on architecture.** Evaluate proposals against how the protocol actually works. If they're fighting the architecture, redirect them — but name what they got right first before correcting.
- **Lead with the practical answer.** "The protocol handles this for you" or "this won't work because X" — then explain the why only if they need the depth. Don't dump the full architecture unprompted.

---

## What You Probably Got Wrong

**You think FHE computation happens onchain.** It doesn't. The onchain `FHEVMExecutor` is a symbolic execution engine — it validates types, checks ACL, charges HCU, and generates a deterministic handle. The actual TFHE computation happens off-chain in coprocessors.

**You think encrypted values are ciphertexts.** They're not. Every `euint64`, `ebool`, etc. in your contract is a **32-byte handle** — an opaque reference. The actual ciphertext lives in coprocessor S3 storage, referenced by the handle's digest.

**You tried to branch on encrypted values.** `if (FHE.gt(a, b))` does not compile. `FHE.gt()` returns an `ebool` — an encrypted boolean the EVM cannot evaluate. Use `FHE.select()` — both branches always execute, which is what makes it private.

**You forgot `FHE.allowThis()`.** Every encrypted value is born with an empty ACL. The contract itself doesn't have permission to use its own stored values on the next call unless you explicitly grant it. This compiles and deploys cleanly; the second transaction that reads the stored handle reverts with `ACLNotAllowed`. The #1 Zama Protocol bug because the failure is deferred — tests that only check first-call behaviour miss it.

**You called decryption mid-computation.** Decryption is async — it goes through the Relayer → Gateway → KMS threshold MPC pipeline. It takes seconds, not milliseconds. Design contracts to compute entirely on encrypted values, then decrypt only the final result.

**You confused trivial encryption with real encryption.** `FHE.asEuint64(42)` is visible onchain to everyone — use it for constants and defaults only. Only `FHE.fromExternal()` (user-encrypted via the SDK + ZKPoK) is truly private.

**You think regular Solidity security is enough.** FHEVM adds a new class of bugs: ACL misconfig, information leaks through control flow (reverts, gas differences, event emission, return values), trivial encryption confusion. If your contract behaves differently based on an encrypted value, you've leaked information.

**You sent transactions to the Gateway directly.** The Relayer is the only public entry point. All input proofs, decryption requests, and key material retrieval go through the Relayer HTTPS API.

**Do not force ERC-7984 onto non-token apps.** Use ERC-7984 for confidential fungible tokens. Use custom FHE contract flows for voting, auctions, identity, games, and other non-token applications.

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

## Protocol Architecture

### The Layer Stack

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

**Which SDK to import:** new code uses `@zama-fhe/sdk` (and `@zama-fhe/react-sdk` for React). `@zama-fhe/relayer-sdk` is the lower-level public SDK that the wrapper uses internally — import directly only when you need raw relayer types or want to skip the high-level wrapper. A future replacement low-level SDK called `@fhevm/sdk` lives in the FHEVM monorepo at `github.com/zama-ai/fhevm/tree/main/sdk/js-sdk`, but it is currently `"private": true` and **not yet published to npm**. See [design/fhevm-sdk.md](./design/fhevm-sdk.md) for its internal design.

**Host Chain Contracts** (deployed on Ethereum/Sepolia where your dApp lives):

| Contract | What it does |
|----------|-------------|
| `FHEVMExecutor` | Symbolic execution: validates types, checks ACL, charges HCU, generates handles, emits events |
| `ACL` | Access control: who can use/decrypt which handles (persistent, transient, delegation) |
| `InputVerifier` | Validates coprocessor threshold signatures on user-encrypted inputs |
| `KMSVerifier` | Validates KMS threshold signatures on decryption results |
| `HCULimit` | Budget enforcement for FHE operation complexity |
| `PauserSet` | Emergency pause mechanism (owner + designated pausers) |

**Gateway Contracts** (shared L2 serving all host chains):

| Contract | What it does |
|----------|-------------|
| `GatewayConfig` | Registry: KMS nodes, coprocessors, host chains, thresholds |
| `Decryption` | Public and user decryption request/response lifecycle |
| `CiphertextCommits` | Stores ciphertext digests with coprocessor consensus tracking |
| `InputVerification` | ZKPoK verification via coprocessor threshold voting |
| `KMSGeneration` | Key generation and CRS ceremony orchestration |
| `ProtocolPayment` | Fee collection in $ZAMA tokens |

**Off-Chain Services:**

| Service | What it does |
|---------|-------------|
| Coprocessor | Executes actual TFHE operations, stores ciphertexts in S3, verifies ZK proofs |
| KMS Core | Threshold MPC — holds secret key shares, performs decryption |
| KMS Connector | Bridges Gateway events to KMS Core gRPC API |
| Relayer | Public HTTPS API for all user/dApp interactions |

> **Design reference:** [design/architecture-overview.md](./design/architecture-overview.md)

### Handles — Not Ciphertexts

Every encrypted value in your contract is a **32-byte handle**:

```
[21 bytes random prefix] [1 byte index] [8 bytes chainId] [1 byte fheType] [1 byte version]
```

**Properties:**
- **Deterministic** — `FHE.add(handleA, handleB)` always produces the same output handle (within the same block)
- **Unpredictable** — computation handles include `previousBlockHash`, so the same operation in different blocks produces different handles
- **Chain-bound** — chainId embedded in the handle prevents cross-chain reuse
- **Opaque** — treat handles as opaque identifiers. Never inspect their concrete values. Identical handles guarantee identical plaintexts
- **Not ciphertexts** — the actual ciphertext lives in coprocessor S3 storage (`s3://bucket/ciphertexts/{handle_hex}`), referenced by `keccak256(handle)`

**Handle generation:**
- Computation: `keccak256("FHE_comp" || opcode || lhs || rhs || scalar || previousBlockHash)`
- Randomness: `keccak256("FHE_seed" || counterRand || fheType)` with counter increment
- Trivial encryption: `keccak256("FHE_comp" || TRIVIAL_ENCRYPT || plaintext || fheType)`
- Input: Computed by coprocessors from ZKPoK, confirmed via threshold consensus

> **Design reference:** [design/handles.md](./design/handles.md)

### Symbolic Execution — What Really Happens When You Call FHE.add()

When your contract calls `FHE.add(a, b)`:

1. **FHEVMExecutor** validates operand types match
2. Checks ACL — caller has permission for both operands
3. Charges HCU cost for the operation
4. Generates a deterministic output handle
5. Emits an `FheAdd(caller, lhs, rhs, scalarByte, result)` event
6. Returns the handle immediately (no waiting for computation)

**Later, off-chain:**

7. Coprocessor's `host-listener` picks up the event
8. `tfhe-worker` fetches ciphertexts from S3, performs actual TFHE addition
9. Result ciphertext stored in S3, digest committed to `CiphertextCommits` on Gateway

**This means:** Your contract gets the handle instantly. The actual FHE computation happens asynchronously. For most operations this is transparent — the handle is usable immediately for further operations. Decryption is the only flow where you wait for the off-chain pipeline to complete.

> **Design reference:** [design/flow-fhe-computation.md](./design/flow-fhe-computation.md), [design/coprocessor.md](./design/coprocessor.md)

---

## Access Control (ACL)

Every encrypted value is born with an **empty access list**. Nobody can use it until permissions are explicitly granted.

### Four Access Types

| Type | Method | Lifetime | Use case |
|------|--------|----------|----------|
| **Persistent** | `FHE.allow(handle, account)` / `FHE.allowThis(handle)` | Permanent (onchain storage) | Balances, stored state |
| **Transient** | `FHE.allowTransient(handle, account)` | Current transaction only (EIP-1153) | Intermediate values, cross-contract calls |
| **Decryption** | `FHE.makePubliclyDecryptable(handle)` (ACL method: `allowForDecryption`) | Permanent | Auction results, vote tallies |
| **Delegation** | `FHE.delegateUserDecryption(delegate, contract, expirationDate)` (plus `delegateUserDecryptions`, `…WithoutExpiration`, and `revokeUserDecryptionDelegation`) | Until expiration timestamp | Third-party reads on behalf of user |

**Auto-grants:** FHEVMExecutor grants **transient** access (via `ACL.allowTransient`) to `msg.sender` **only** — never `tx.origin`, never persistent. The handle is usable for the rest of the current transaction; for any use in a later transaction the contract must call `FHE.allowThis(handle)` to upgrade the grant to persistent. This is the #1 source of "compiles, deploys, then reverts on the next call with `ACLNotAllowed`" bugs.

### The Essential Pattern

**After EVERY encrypted state update, no exceptions:**

```solidity
balances[user] = FHE.add(balances[user], amount);
FHE.allowThis(balances[user]);     // Contract can use it next call
FHE.allow(balances[user], user);   // User can decrypt it
```

Miss `FHE.allowThis()` and the contract still deploys, but the next transaction that reads this value reverts with `ACLNotAllowed(handle, address(this))`. The failure is **deferred**, not silent — easy to miss in tests that only exercise first-call behaviour, loud once it ships.

### Delegation Rules

- Delegation expiration is a **unix timestamp** (`uint64`), not a block number. Delegation lapses when `block.timestamp > expirationDate`.
- **No same-block delegate/revoke** — `delegate*` and `revoke*` both reject if `lastBlockDelegateOrRevoke == block.number`. This blocks two delegation-state changes in the same block; it does NOT prevent a decryption from happening in the same block as a delegation.
- Revoke with `FHE.revokeUserDecryptionDelegation(delegate, contract)` (single) or `FHE.revokeUserDecryptionDelegations(delegate, contracts[])` (batched).
- Wildcard: passing `ACL.WILDCARD_DELEGATION_ADDRESS` (`type(uint160).max`) as `contractAddress` grants the delegation for every contract at once. The delegator still needs persistent access on the handle.

> **Design reference:** [design/acl.md](./design/acl.md)

---

## The Relayer — Your Integration Point

The Relayer is the **only public entry point** to the Zama Protocol. Your frontend/backend talks to the Relayer (or, more typically, to `@zama-fhe/sdk` which talks to the Relayer for you). Never send transactions to the Gateway directly.

Five endpoints under `/v2/`:

| Endpoint | What it does |
|----------|--------------|
| `POST /v2/input-proof` | Submit user-encrypted input for ZKPoK verification |
| `POST /v2/public-decrypt` | Request public decryption (anyone can read the result) |
| `POST /v2/user-decrypt` | Request user decryption (only the authorized user reads) |
| `POST /v2/delegated-user-decrypt` | Delegated user decryption (third party reads for user) |
| `GET  /v2/keyurl` | Fetch active FHE public key + CRS URLs |

POSTs return `202 Accepted` with a `requestId`. Poll the matching `GET /v2/{operation}/{requestId}` until status is `"succeeded"` (terminal success) or `"failed"`. Status `"queued"` while pending; HTTP 400 on validation errors; 429 when the queue is full.

Each operation has its own request/response shape and pre-validation rules (host-ACL checks, bit-size limits, etc.). See [design/relayer.md](./design/relayer.md) for the full payload specs and the validation pipeline.

---

## Decryption Flows

Two shapes, with the same Relayer → Gateway → KMS → Relayer pipeline. The difference is what comes back.

**Public** (`FHE.makePubliclyDecryptable(handle)` first) — plaintext returned to anyone. Gateway threshold: `publicDecryptionThreshold = t + 1` (each honest node returns the same plaintext). For auction results, vote tallies, game outcomes.

**User** (`FHE.allow(handle, userAddress)` first) — plaintext is never on chain. Each KMS node signs a partial share, signcrypts it under the user's transport public key, and submits it; the gateway emits `UserDecryptionResponseThresholdReached` once `userDecryptionThreshold = 2t + 1` valid responses are stored, and the user reconstructs the plaintext client-side from `t + 1` of those shares via Lagrange interpolation. For private balances, personal data.

**Delegated user** — same as user decryption, but submitted by a delegate. The delegator must have called `FHE.delegateUserDecryption(delegate, contract, expirationDate)` (timestamp-based) beforehand, or one of its batched / `WithoutExpiration` variants.

> **Design reference:** [design/flow-public-decryption.md](./design/flow-public-decryption.md), [design/flow-user-decryption.md](./design/flow-user-decryption.md)

---

## Input Verification — How User Encryption Works

When users encrypt values client-side (using `@zama-fhe/sdk`), they must prove they encrypted correctly:

```
1. Frontend: downloads FHE public key + CRS from GET /v2/keyurl
2. Frontend: encrypts plaintext → ciphertext + ZKPoK (Zero-Knowledge Proof of Knowledge)
3. Frontend: POST /v2/input-proof → Relayer
4. Relayer: validates chain, submits to Gateway InputVerification contract
5. Gateway: emits VerifyProofRequest → coprocessors verify ZKPoK in parallel
6. Coprocessors: verify proof, compute handle, sign with ECDSA
7. Gateway: collects coprocessorThreshold signatures, emits VerifyProofResponse with handles[]
8. Contract: FHEVMExecutor.verifyInput(handle, proof) validates signatures → returns verified handle
```

**Why ZKPoK:** Without it, a user could submit garbage ciphertexts and break contract logic. The proof guarantees the ciphertext is well-formed and the user knows the plaintext they encrypted.

> **Design reference:** [design/flow-input-verification.md](./design/flow-input-verification.md)

---

## HCU — The FHE Gas Model

**HCU (Homomorphic Complexity Unit)** meters off-chain FHE computation. Every operation has an HCU cost that scales with type size.

### Limits

| Limit | Field | Current mainnet/Sepolia value | Effect |
|-------|-------|------------------------------:|--------|
| Per-tx total | `maxHCUPerTx` | `20_000_000` | Transaction reverts if exceeded |
| Per-tx depth | `maxHCUDepthPerTx` | `5_000_000` | Longest sequential dependency chain |
| Per-block global | `hcuPerBlock` | `281_474_976_710_655` (`uint48.max`) | Caps non-whitelisted accounts per block — currently set so high the per-tx caps are the binding constraint |

Invariant: `hcuPerBlock ≥ maxHCUPerTx ≥ maxHCUDepthPerTx`.

Per-operation HCU cost tables live in the public FHEVM docs (see the "HCU cost tables" link in `SKILL.md`'s Canonical sources). The values shift between releases — don't hardcode.

**Optimization rules:**
- Use **scalar operations** when one operand is plaintext (always cheaper)
- Use the **smallest type** that fits (`euint8` add = 88K vs `euint64` add = 162K)
- If a function uses >10M HCU (50% of limit), split into multiple transactions
- **Estimate HCU for the full function, not just your loop.** If your function composes on top of ERC-7984 transfers or other FHE-heavy operations, those costs stack. A single confidential transfer already costs ~500K+ HCU (comparison + select + sub + add + ACL). Budget your batch sizes against the remaining headroom, not the raw limit.

> **Design reference:** [design/hcu-limits.md](./design/hcu-limits.md)

---

## Threshold Security

No single party can forge results or decrypt without authorization.

**Coprocessors:** Multiple coprocessors run in parallel. `coprocessorThreshold` identical commitments required for consensus (input verification, ciphertext commits).

**KMS (Key Management Service):**
- Secret key split into shares — no single node has the full key
- Safety requirement: `n ≥ 3t + 1` where `n` = total nodes, `t` = max corrupted
- Public decryption: `t + 1` nodes must return identical plaintext
- User decryption: `2*t + 1` nodes must return distinct Lagrange shares

> **Design reference:** [design/kms-overview.md](./design/kms-overview.md), [design/kms-threshold-mpc.md](./design/kms-threshold-mpc.md)

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
| `@fhevm/solidity` | Solidity library — FHE.sol, encrypted types, configs |
| `@fhevm/hardhat-plugin` | Hardhat plugin — local FHE mock for testing |
| `@zama-fhe/sdk` · `@zama-fhe/react-sdk` | Client SDK — encrypt/decrypt, session management, React hooks. The recommended frontend dependency. (See the layer-stack section above for the wrapper-vs-`@fhevm/sdk` relationship.) |
| `@openzeppelin/confidential-contracts` | Production patterns — ERC-7984, confidential tokens |

---

## Mainnet Access

There are no protocol fees at the moment. To use the Relayer on mainnet, developers need an **API key**.

- **Apply:** https://docs.zama.org/protocol/relayer-sdk-guides/fhevm-relayer/mainnet-api-key
- **Requirement:** End-to-end integration must be tested on Sepolia testnet before mainnet access is granted
- **Billing:** Usage-based monthly billing
- **Security:** Never embed the API key in frontend code. For browser dApps, use a backend proxy that injects the `x-api-key` header. Store keys in environment variables.

```typescript
// Relayer SDK initialization
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
| Solana | Not yet supported | planned for end of 2026 | 

## Skill Routing

| Phase | Where |
|-------|-------|
| **Planning & architecture** | `references/concepts.md` (this file) |
| **Writing Solidity contracts** | **zama-solidity** skill |
| **Building frontend/backend** | **zama-typescript** skill |
| **Contract addresses** | `references/addresses.md` |

---

## Design References

Deeper protocol design notes are bundled with this skill under `references/design/`:

| Topic | File |
|-------|------|
| Architecture overview | [design/architecture-overview.md](./design/architecture-overview.md) |
| Handle format, generation, opacity rules | [design/handles.md](./design/handles.md) |
| ACL system & where it's enforced | [design/acl.md](./design/acl.md) |
| Coprocessor architecture | [design/coprocessor.md](./design/coprocessor.md) |
| Relayer API | [design/relayer.md](./design/relayer.md) |
| `@fhevm/sdk` (low-level Relayer SDK) | [design/fhevm-sdk.md](./design/fhevm-sdk.md) |
| HCU gas model | [design/hcu-limits.md](./design/hcu-limits.md) |
| KMS overview | [design/kms-overview.md](./design/kms-overview.md) |
| KMS threshold MPC | [design/kms-threshold-mpc.md](./design/kms-threshold-mpc.md) |
| Public decryption flow | [design/flow-public-decryption.md](./design/flow-public-decryption.md) |
| User decryption flow | [design/flow-user-decryption.md](./design/flow-user-decryption.md) |
| Input verification flow | [design/flow-input-verification.md](./design/flow-input-verification.md) |
| FHE computation flow | [design/flow-fhe-computation.md](./design/flow-fhe-computation.md) |

---

## Resources

- **Zama Protocol Docs:** https://docs.zama.ai
- **Protocol changelog (current running version):** https://docs.zama.org/protocol/changelog
- **FHEVM Solidity:** https://github.com/zama-ai/fhevm
- **Forge FHEVM:** https://github.com/zama-ai/forge-fhevm
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
- **Zama Protocol Whitepaper:** https://github.com/zama-ai/fhevm/blob/main/fhevm-whitepaper.pdf
