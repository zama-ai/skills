# Zama TypeScript - SDK Integration

Integrate the Zama FHE SDK into browser apps, React apps, Node.js backends, browser extensions, and local Hardhat environments. React Native is not directly supported; use a Node backend and proxy.

This file is a router for SDK usage. Choose one environment setup first, then load only the task reference that matches the work.

For protocol-level or architectural questions (Relayer/Gateway/KMS behavior), load the **zama-protocol** skill instead.

## Canonical docs

The hosted SDK docs are now live at **https://docs.zama.org/protocol/sdk** — that's the authoritative reference. Source is at `https://github.com/zama-ai/sdk` (the wrapper SDK monorepo, currently `@zama-fhe/sdk@3.x`).

When a detail is missing from the hosted docs, inspect:
- Runnable examples — `https://github.com/zama-ai/sdk/tree/main/examples/`
- Generated typings — `node_modules/@zama-fhe/sdk/dist/esm/index.d.ts` and `node_modules/@zama-fhe/react-sdk/dist/esm/index.d.ts`

## Choose one environment setup

- `setups/react-wagmi.md` - React app using `@zama-fhe/react-sdk` with the wagmi adapter
- `setups/browser-viem.md` - browser app using `@zama-fhe/sdk` with viem
- `setups/browser-ethers.md` - browser app using `@zama-fhe/sdk` with ethers
- `setups/node-backend.md` - Node.js scripts, servers, workers, and custom signer backends
- `setups/extension-mv3.md` - MV3 extension with persistent permit credentials
- `setups/localhost-setup.md` - cleartext mode for local Hardhat, Hoodi, InGen, or other unsupported-chain testing

## Mental model

```text
ZamaSDK <- Relayer transport  (FHE backend — web()/node()/cleartext(); runs encrypt/decrypt in a worker)
        <- Signer + Provider  (wallet signTypedData/writeContract; chain reads/getChainId)
        <- Storage            (FHE keypair cache; permitStorage caches the wallet permit)
```

Build the whole thing with `createConfig({ chains, relayers, storage })` — from `@zama-fhe/sdk/viem`, `@zama-fhe/sdk/ethers`, or `@zama-fhe/react-sdk/wagmi` — then `new ZamaSDK(config)`. `createConfig` builds the signer/provider for you and wires chain switching internally; there is no manual `getChainId`.

## Environment matrix

| Environment | Relayer transport | Config builder | Storage |
|---|---|---|---|
| React + wagmi | `web()` (`@zama-fhe/sdk/web`) | `createConfig` (`@zama-fhe/react-sdk/wagmi`) | `indexedDBStorage` (+ `permitStorage`) |
| Browser + viem | `web()` | `createConfig` (`@zama-fhe/sdk/viem`) | `indexedDBStorage` |
| Browser + ethers | `web()` | `createConfig` (`@zama-fhe/sdk/ethers`) | `indexedDBStorage` |
| MV3 extension | `web()` | `createConfig` (`/viem` or `/ethers`) | `storage: indexedDBStorage`, `permitStorage: chromeSessionStorage` |
| Node.js script / CLI | `node()` (`@zama-fhe/sdk/node`) | `createConfig` (`/viem` or `/ethers`) | `memoryStorage` |
| Node.js server (concurrent requests) | `node()` | same | `asyncLocalStorage` (`@zama-fhe/sdk/node`) |
| Local Hardhat / cleartext | `cleartext()` (`@zama-fhe/sdk` or `/node`) | any | `memoryStorage` |
| React Native / mobile | Not supported - proxy via Node backend | | |

The wagmi adapter (`createConfig` from `@zama-fhe/react-sdk/wagmi`) is the recommended React path — it derives the SDK signer/provider from the wagmi `Config` and subscribes to connection changes, so no "build a ViemSigner after connect" boundary is needed.

Chain presets are exported from `@zama-fhe/sdk/chains`: `mainnet`, `sepolia`, `hoodi`, `ingenTestnet`, `bscTestnet`, `hardhat`, `anvil`. Spread one and override `relayerUrl` / `network` / `auth` as needed (use `.id`, not `.chainId`):

```ts
import { sepolia } from "@zama-fhe/sdk/chains";
import { web } from "@zama-fhe/sdk/web";

const zamaSepolia = {
  ...sepolia,
  relayerUrl: "https://your-app.com/api/relayer/11155111", // browser: proxy via backend
  network: "https://sepolia.infura.io/v3/YOUR_KEY",
};

// createConfig({ chains: [zamaSepolia], /* clients or signer */, storage,
//                relayers: { [zamaSepolia.id]: web() } })
```

## Choose one task reference

| Need | Read |
|---|---|
| Package overview, sub-paths, signer choice, `GenericSigner` | `packages-and-signers.md` |
| ERC-7984 token integration: shield, transfer, balance, unshield, wrapper discovery | `tokens.md` |
| Custom FHE contracts: encrypt input, read handles, decrypt output | `custom-contracts.md` |
| Permits, `useGrantPermit`, `useRevokePermits`, delegation, TTLs | `permissions.md` |
| React provider, storage, hook selection, decrypt UX | `react.md` |
| Migrating older SDK / relayer / FHEVM-style integrations | `packages-and-signers.md` |

## Universal gotchas

- **Package landscape.** Install `@zama-fhe/sdk` explicitly. `@zama-fhe/react-sdk` requires it as a peer dependency and pnpm will not install peers automatically.
- **Sepolia needs no relayer proxy.** The `sepolia` chain preset's `relayerUrl` already points at the public Zama testnet relayer. Spread `sepolia` as-is and leave `relayerUrl` alone. Only override it on mainnet.
- **Relayer API key (mainnet only).** Browser apps must proxy mainnet relayer requests through their own backend to keep the API key server-side — the proxy injects it as the `x-api-key` header. Node scripts put `auth: { __type: "ApiKeyHeader", value: process.env.RELAYER_API_KEY }` on the chain preset (note the **double-underscore** `__type` — that's the discriminator the relayer-sdk type expects). The Zama-hosted relayer accepts the key **only** as `ApiKeyHeader` (`x-api-key`); `BearerToken` / `ApiKeyCookie` are for self-hosted relayers or your own proxy — see `setups/node-backend.md`.
- **COOP/COEP headers required for browser.** The `web()` relayer uses a Web Worker with WASM + `SharedArrayBuffer`. Serve with `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`. Vite: `server.headers`. Next.js: `async headers()` in config.
- **Use the high-level token API for ERC-7984.** `sdk.createToken(addr)` returns a `Token` (`.balanceOf`, `.confidentialTransfer`, operators). For shield/unshield use `sdk.createWrappedToken(addr)` → `WrappedToken` (`.shield`, `.unshield`, `.allowance`). Use `useEncrypt` / `useDecryptValues` for custom FHE contracts such as auctions and voting.
- **Encrypt returns ABI-ready hex.** `encrypt()` returns `{ encryptedValues, inputProof }` already as `0x` hex (`encryptedValues` are `bytes32`, `inputProof` is `bytes`). Pass them straight to contract calls — do **not** run them through `bytesToHex` / `hexlify`.
- **Ciphertexts bind to one target contract.** The `contractAddress` in `encrypt()` must be the contract that will consume it. Encrypt per hop.
- **Do not treat the SDK as token-only.** Token helpers are the happy path for ERC-7984, but the same stack also supports custom FHE contracts. Route those cases to `custom-contracts.md`.

## Canonical doc paths

Hosted at `https://docs.zama.org/protocol/sdk`:

- **Tutorials** — Quick start · First confidential dApp · Wallet & exchange integration
- **Guides** — Configuration · Authentication · Relayer API keys · Shield · Transfer privately · Unshield · Check balances · Handle errors · Activity feeds · Node.js backend · Web extensions · Local development · Next.js SSR · Operator approvals · Encrypt & decrypt
- **API reference (SDK)** — `ZamaSDK`, `createConfig`, `Token`, `WrappedToken`, `WrappersRegistry`, `web` / `node` / `cleartext` relayer transports, `ViemSigner`, `EthersSigner`, `WagmiSigner`, `GenericSigner` / `GenericProvider`, `GenericStorage`, chain presets (`@zama-fhe/sdk/chains`), errors, contract builders, event decoders, delegated decryption
- **API reference (React)** — `ZamaProvider` + the full hook surface (`useShield`, `useConfidentialBalance(s)`, `useConfidentialTransfer(From)`, `useUnshield(All)`, `useResumeUnshield`, `useUnwrap(All)`, `useFinalizeUnwrap`, `useGrantPermit`, `useHasPermit`, `useRevokePermits`, `useClearCredentials`, `useApproveUnderlying`, `useConfidentialSetOperator`, `useEncrypt`, `useDecryptValues`, `useDecryptPublicValues`, `useDelegatedDecryptValues`, `useDelegateDecryption`, `useRevokeDelegation`, `useDelegationStatus`, `useDecryptBalanceAs`, `useBatchDecryptBalancesAs`, `useToken`, `useWrappedToken`, `useZamaSDK`, plus wrapper-registry / discovery hooks)
