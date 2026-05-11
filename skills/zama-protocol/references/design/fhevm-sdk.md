# `@fhevm/sdk` — the future low-level Relayer SDK

> **Status: currently `"private": true` — not yet published to npm.** This page describes the SDK's internal design as it exists in the FHEVM monorepo. It's expected to eventually replace `@zama-fhe/relayer-sdk` as the public lower-level SDK that `@zama-fhe/sdk` uses internally, but that hand-off hasn't shipped. For today, user-facing low-level needs go through `@zama-fhe/relayer-sdk` (or the high-level `@zama-fhe/sdk` wrapper). Treat this file as a design reference, not an install guide.

`@fhevm/sdk` is the JavaScript/TypeScript SDK design that will eventually talk to the Zama Protocol Relayer as the lower-level engine for `@zama-fhe/sdk`. The shape below reflects the source in the FHEVM monorepo; method names and APIs may shift before publication.

- Source: [zama-ai/fhevm/sdk/js-sdk](https://github.com/zama-ai/fhevm/tree/main/sdk/js-sdk)
- License: BSD-3-Clause-Clear
- Node: ≥ 22 (design target)

## What it does

Three operations, mirroring the Relayer's three operation classes:

| Operation | What it does | WASM used |
|-----------|--------------|-----------|
| **Encrypt** | Client-side TFHE encryption + ZKPoK generation. Produces external encrypted handles and an `inputProof` you pass to your contract. | TFHE (~5 MB) |
| **Decrypt (private)** | Generates a transport keypair, signs an EIP-712 decryption permit, requests signcrypted shares from the Relayer, decrypts and reconstructs the plaintext locally. Plaintext never leaves the browser. | TKMS (~600 KB) |
| **Read public values** | Reads values the contract has marked publicly decryptable via `FHE.makePubliclyDecryptable` / `ACL.allowForDecryption`. | None (relayer + RPC) |

Both ethers v6 and viem are supported with identical APIs — the choice is a single import path.

## Clients

Four factory functions, each pre-composed for a use case. Pick the smallest one that fits the page to minimise WASM download:

```ts
import { createFhevmClient }        from "@fhevm/sdk/ethers"; // or @fhevm/sdk/viem
import { createFhevmEncryptClient } from "@fhevm/sdk/ethers";
import { createFhevmDecryptClient } from "@fhevm/sdk/ethers";
import { createFhevmBaseClient }    from "@fhevm/sdk/ethers";
```

| Factory | Capabilities | WASM loaded |
|---------|--------------|-------------|
| `createFhevmClient`        | Encrypt + decrypt + read public values | TFHE + TKMS |
| `createFhevmEncryptClient` | Encrypt + read public values           | TFHE        |
| `createFhevmDecryptClient` | Decrypt + read public values           | TKMS        |
| `createFhevmBaseClient`    | Read public values; extend manually    | None        |

WASM loads **lazily** on first use. Call `await client.init()` to preload before user interaction. The matching runtime initialisers are exported as `initFhevmRuntime` / `initFhevmEncryptRuntime` / `initFhevmDecryptRuntime` for advanced setups that build a runtime explicitly.

## Quick start

```ts
import { setFhevmRuntimeConfig, createFhevmClient } from "@fhevm/sdk/ethers";
import { sepolia } from "@fhevm/sdk/chains";
import { ethers } from "ethers";

setFhevmRuntimeConfig({ numberOfThreads: 4 });

const provider = new ethers.JsonRpcProvider("https://ethereum-sepolia-rpc.publicnode.com");
const client = createFhevmClient({ chain: sepolia, provider });
```

**Encrypt:**

```ts
const encrypted = await client.encryptValues({
  contractAddress: "0x...",
  userAddress:     "0x...",
  values: [
    { type: "uint32", value: 42 },
    { type: "bool",   value: true },
  ],
});
await contract.myFunction(
  encrypted.encryptedValues[0],
  encrypted.encryptedValues[1],
  encrypted.inputProof, // shared proof for all values in the batch
);
```

For a single value, `client.encryptValue({ ... })` is the convenience wrapper.

**Decrypt private:**

```ts
const transportKeypair = await client.generateTransportKeypair();

const signedPermit = await client.signDecryptionPermit({
  transportKeypair,                          // not "e2eTransportKeypair"
  contractAddresses: ["0x..."],
  startTimestamp:    Math.floor(Date.now() / 1000),
  durationDays:      7,
  signerAddress:     await signer.getAddress(),
  signer,
});

// Batch
const results = await client.decryptValues({
  transportKeypair,
  signedPermit,
  encryptedValues: [
    { encryptedValue: handle, contractAddress: "0x..." },
  ],
});
results[0].value;   // number | bigint | boolean | "0x..."
results[0].fheType; // "euint32" | "ebool" | "eaddress" | ...

// Single value
const result = await client.decryptValue({
  transportKeypair,
  signedPermit,
  encryptedValue: handle,
  contractAddress: "0x...",
});

// From [{handle, contract}, ...] pairs (matches the Relayer payload shape)
const fromPairs = await client.decryptValuesFromPairs({
  transportKeypair,
  signedPermit,
  handleContractPairs: [{ handle, contractAddress: "0x..." }],
});
```

**Read public values:**

```ts
// Plain read
const values = await client.readPublicValues({
  encryptedValues: [handle],
});
values[0].value;
values[0].fheType;

// Single value
const single = await client.readPublicValue({ encryptedValue: handle });

// With KMS signatures — useful when you need to forward the proof on-chain
// to FHE.checkSignatures(handlesList, cleartexts, decryptionProof)
const withProof = await client.readPublicValuesWithSignatures({
  encryptedValues: [handle],
});
withProof.values[0].value;
withProof.decryptionProof; // pass into Solidity FHE.checkSignatures
```

## Persistence helpers

The transport keypair and decryption permit are designed to be reused across pages and sessions. The SDK ships symmetric `parse` / `serialize` helpers so you can persist them safely:

```ts
import {
  parseTransportKeypair,
  serializeTransportKeypair,
  parseSignedDecryptionPermit,
  serializeSignedDecryptionPermit,
} from "@fhevm/sdk/actions/base"; // or via client.{parse,serialize}…

const blob = serializeTransportKeypair(transportKeypair);     // safe to store
const restored = await parseTransportKeypair(blob);           // back to a usable keypair
```

The internal key material is kept in private fields and accessed only through symbol-keyed accessors — application code never sees the raw private key.

## Import paths

Tree-shaking is per-subpath — only what you import gets bundled.

| Path | Surface |
|------|---------|
| `@fhevm/sdk/ethers` | Client factories + `setFhevmRuntimeConfig`, `initFhevmRuntime`, etc. (ethers v6) |
| `@fhevm/sdk/viem`   | Same surface as `/ethers`, for viem |
| `@fhevm/sdk/chains` | Built-in chain definitions (`mainnet`, `sepolia`) |
| `@fhevm/sdk/actions/base`    | Standalone primitives — `readPublicValues`, `signDecryptionPermit`, parse/serialize keypair + permit, `fetchFheEncryptionKeyBytes`, ACL checks |
| `@fhevm/sdk/actions/encrypt` | Standalone encrypt actions (`encryptValues`, `generateZkProof`) |
| `@fhevm/sdk/actions/decrypt` | Standalone decrypt + keypair actions (`decryptValues`, `decryptValuesFromPairs`, `generateTransportKeypair`) |
| `@fhevm/sdk/actions/chain`   | EIP-712 creation/verification, `signDecryptionPermit`, keypair ops |
| `@fhevm/sdk/actions/host`    | Direct reads of ACL, KMSVerifier, InputVerifier, FHEVMExecutor |

The `actions/*` paths expose every operation as a standalone function (first arg is the client) — useful when you don't want a long-lived client, or when bundling for serverless.

## Internal architecture

```text
Application code
    │
Adapter layer (ethers/ or viem/)   ← seals adapter client into TrustedClient,
    │                                 manages runtime lifecycle, exposes factories
Core layer (core/)                 ← actions, clients (decorator composition),
    │                                 modules (encrypt, decrypt, relayer), types
WASM layer (wasm/)                 ← TFHE bindings (encryption),
                                      TKMS bindings (decryption)
```

Dependency direction is strictly top-down — Core never imports from adapters; actions never import from decorators; modules never import from actions. This is what makes the dual adapter (ethers + viem) and the four pre-composed clients work without code duplication.

Runtime module composition uses TypeScript's type system to track which modules are loaded:

```ts
// Runtime starts with EthereumModule + RelayerModule and is extended:
const runtime = getAdapterRuntime()
  .extend(encryptModule)    // adds TFHE WASM
  .extend(decryptModule);   // adds TKMS WASM

// encrypt action requires WithEncrypt — compile-time error if module missing
async function encryptValues(fhevm: Fhevm<FhevmChain, WithEncrypt>, ...): Promise<...>
```

## Data flow under the hood

### Encryption

```text
encryptValues()
  ├─ fetchFheEncryptionKeyBytes()      → fetch ~50 MB public key (cached)
  ├─ generateZkProof()
  │    └─ TFHE WASM: build packed ciphertext + ZKPoK            (CPU intensive)
  └─ fetchVerifiedInputProof()
       ├─ relayer.fetchCoprocessorSignatures()  → POST /v2/input-proof, poll
       └─ on-chain coprocessor-signature verification via RPC
```

### Private decryption

```text
decryptValues()
  ├─ fetchKmsSignedcryptedShares()
  │    ├─ checkUserAllowedForDecryption()  → ACL.isAllowed via RPC
  │    └─ relayer.fetchUserDecrypt()       → POST /v2/user-decrypt, poll
  └─ decryptKmsSignedcryptedShares()
       └─ TKMS WASM: signcryption decap + Lagrange reconstruct
```

### Public read

```text
readPublicValues()
  ├─ validation (non-empty, bit-limit, chain ID)
  ├─ checkAllowedForDecryption()  → ACL.isAllowedForDecryption via RPC
  ├─ relayer.fetchPublicDecrypt() → POST /v2/public-decrypt, poll
  └─ createPublicDecryptionProof() → KMS-signature verification via RPC
```

## Browser requirements

Multi-threaded TFHE encryption uses `SharedArrayBuffer`, which requires cross-origin isolation:

```text
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

Without those headers the SDK falls back to single-threaded mode automatically — slower but correct.

## Supported chains

| Chain | ID | Status |
|-------|----|--------|
| Ethereum mainnet | 1 | Production |
| Ethereum Sepolia | 11155111 | Testnet |

Custom chains can be defined for local Hardhat or dev networks — see the SDK's `docs/chains.md`.

## When this matters today

Right now: it doesn't, for end users. `@fhevm/sdk` is private. The public surface remains `@zama-fhe/sdk` (high-level) and `@zama-fhe/relayer-sdk` (lower-level, what the wrapper uses internally).

This page is useful if you're:
- Contributing to the FHEVM monorepo itself.
- Building a wrapper that needs to anticipate the future low-level surface.
- Trying to understand the design direction for the lower-level SDK.

For shipping apps today: use `@zama-fhe/sdk` — see the layer-stack section of `concepts.md`.
