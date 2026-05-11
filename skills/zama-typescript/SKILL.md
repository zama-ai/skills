---
name: zama-typescript
description: Integrate the Zama FHE SDK into TypeScript apps — React, browser, Node.js, MV3 extensions. Use when the user mentions `@zama-fhe/sdk`, `@zama-fhe/react-sdk`, `@fhevm/sdk` (the low-level Relayer SDK), the legacy `@zama-fhe/relayer-sdk`, ViemSigner, EthersSigner, RelayerWeb, RelayerNode, ZamaProvider, createFhevmClient, encryptValues, decryptValues, readPublicValues, generateTransportKeypair, useShield, useConfidentialBalance, useEncrypt, useUserDecrypt, useAllow, or any TypeScript/JavaScript code that encrypts inputs, reads encrypted handles, or decrypts FHE outputs. Also use for SDK setup, signer choice, session/delegation patterns, and React hook selection. For protocol concepts, architecture, and the low-level SDK design deep-dive, load the zama-protocol skill. For Solidity contract development, load the zama-solidity skill.
---

# Zama TypeScript — SDK Integration

Integrate the Zama FHE SDK into browser apps, React apps, Node.js backends, browser extensions, and local setup environments. React Native is not directly supported; use a Node backend and proxy.

**Before starting:** load the **zama-protocol** skill and read the universal gotchas — they cover protocol-level bugs that apply to all FHEVM work. What follows here is TypeScript/SDK-specific.

## Which SDK?

There are two TypeScript packages in this stack — pick deliberately:

- **`@zama-fhe/sdk`** — recommended high-level wrapper. Adds session management, token helpers, React hooks (`@zama-fhe/react-sdk`), better error messages. Most of this skill (signers, `ZamaSDK`, `RelayerWeb` / `RelayerNode`, storage backends, `SepoliaConfig`, hooks, token API) documents this package. Repo: github.com/zama-ai/sdk · docs: docs.zama.org/protocol/sdk.
- **`@fhevm/sdk`** — the low-level Relayer SDK that `@zama-fhe/sdk` wraps internally. Standalone action functions, narrow client factories (`createFhevmClient` / `EncryptClient` / `DecryptClient` / `BaseClient`), tightest possible bundles. Use it directly when you need raw `encryptValues` / `decryptValues` / `readPublicValues`, custom runtime composition, or are writing a wrapper of your own. For the full surface, see the **zama-protocol** skill's `references/design/fhevm-sdk.md`.
- **`@zama-fhe/relayer-sdk`** — legacy. Being phased out in favour of `@fhevm/sdk`. Migrate when convenient.

---

## References

This file is a router for SDK usage. Choose one environment setup first, then load only the task reference that matches the work. Load on demand — don't read them all up front.

### Environment setups (pick one)

| Environment | File |
|-------------|------|
| React + wagmi | `references/typescript/setups/react-wagmi.md` |
| Browser + viem | `references/typescript/setups/browser-viem.md` |
| Browser + ethers | `references/typescript/setups/browser-ethers.md` |
| Node.js (scripts, servers, workers) | `references/typescript/setups/node-backend.md` |
| MV3 browser extension | `references/typescript/setups/extension-mv3.md` |
| Local Setup / cleartext | `references/typescript/setups/localhost-setup.md` |

### Task references (pick as needed)

| Task | File |
|------|------|
| SDK mental model, environment matrix, universal TS gotchas | `references/typescript/typescript.md` |
| Package overview, sub-paths, signer choice, GenericSigner | `references/typescript/sdk-package-and-signers.md` |
| ERC-7984 token flows: shield, transfer, balance, unshield | `references/typescript/sdk-token-flows.md` |
| Custom FHE contracts: encrypt input, read handles, decrypt | `references/typescript/sdk-custom-contract-flows.md` |
| Session signatures, useAllow, useRevoke, delegation, TTLs | `references/typescript/sdk-permissions-and-sessions.md` |
| React provider, storage, hook selection, decrypt UX | `references/typescript/react-sdk.md` |
| Verified contract addresses | `references/addresses.md` — **never guess addresses** |

---

## TypeScript-specific reminders

These supplement the universal gotchas in the zama-protocol skill.

- **COOP/COEP headers required for browser.** `RelayerWeb` uses a Web Worker with WASM + `SharedArrayBuffer`. Serve with `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`. Vite: `server.headers`. Next.js: `async headers()` in config.

- **Install `@zama-fhe/sdk` explicitly.** `@zama-fhe/react-sdk` requires it as a peer dependency and pnpm will not install peers automatically.

- **Sepolia needs no relayer proxy.** `SepoliaConfig.relayerUrl` already points at the public Zama testnet relayer. Only override `relayerUrl` on mainnet (proxy through your backend to protect the API key).

- **Ciphertexts bind to one target contract.** The `contractAddress` in `encrypt()` must be the contract that will consume it. Encrypt per hop.

- **Encrypt → ABI conversion.** `encrypt()` returns `handles: Uint8Array[]` and `inputProof: Uint8Array`. Wrap with viem `bytesToHex` or `ethers.hexlify` before passing to contract calls — ABIs expect `bytes32` or `bytes`.

- **Do not trigger decrypt on render.** Gate decrypting reads behind `useIsAllowed` / `isAllowed`. If missing, show an explicit button calling `useAllow` / `allow`. Prevents surprise wallet popups.

- **Do not use `WagmiSigner`** from `@zama-fhe/react-sdk/wagmi` until the upstream bundling issue is fixed. Use wagmi for UI/account state and build a `ViemSigner` after connect.

- **Do not treat the SDK as token-only.** Token helpers are the happy path for ERC-7984, but `useEncrypt` / `useUserDecrypt` support custom FHE contracts (voting, auctions, identity). Route those to `references/typescript/sdk-custom-contract-flows.md`.

## Canonical sources

- **`@zama-fhe/sdk` repo:** https://github.com/zama-ai/sdk
- **`@zama-fhe/sdk` docs:** https://docs.zama.org/protocol/sdk
- **`@zama-fhe/sdk` examples:** https://github.com/zama-ai/sdk/tree/main/examples/
- **`@fhevm/sdk` (low-level):** https://github.com/zama-ai/fhevm/tree/main/sdk/js-sdk
