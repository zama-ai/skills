# Zama TypeScript — SDK Integration

Integrate the Zama FHE SDK into any TypeScript environment: browser, React, Node.js backend, browser extension, local Hardhat. React Native is not directly supported — run a Node backend and proxy.

This file covers the mental model, environment matrix, and universal gotchas. Pair it with **one** per-environment setup file from the sibling `setups/` folder (default: `setups/react-wagmi.md`):

- `setups/react-wagmi.md` / `setups/browser-viem.md` / `setups/browser-ethers.md` — browser
- `setups/node-backend.md` — Node.js (also: proxy for React Native)
- `setups/extension-mv3.md` — MV3 browser extension
- `setups/local-hardhat.md` — local dev with `RelayerCleartext`

**Canonical docs** live at `github.com/zama-ai/sdk` under `docs/gitbook/src/`. Each setup file points at the specific page. When a detail isn't covered, read the doc page directly (or `node_modules/@zama-fhe/sdk/dist/esm/index.d.ts` as a fallback).

## Mental model

```
ZamaSDK ← Relayer  (FHE backend — runs encrypt/decrypt in a worker)
        ← Signer   (wallet — getChainId, signTypedData, writeContract)
        ← Storage  (FHE keypair cache; sessionStorage caches wallet sig)
```

Instantiate the signer **first**, then pass `getChainId: () => signer.getChainId()` into the relayer. The relayer switches FHE workers automatically when the chain changes.

## Environment matrix

| Environment | Relayer | Signer | Storage |
|---|---|---|---|
| React + wagmi | `RelayerWeb` | `WagmiSigner` (`@zama-fhe/react-sdk/wagmi`) | `indexedDBStorage` |
| Browser + viem | `RelayerWeb` | `ViemSigner` (`@zama-fhe/sdk/viem`) | `indexedDBStorage` |
| Browser + ethers | `RelayerWeb` | `EthersSigner({ ethereum: window.ethereum })` | `indexedDBStorage` |
| MV3 extension | `RelayerWeb` | `ViemSigner` / `EthersSigner` | `storage: indexedDBStorage`, `sessionStorage: chromeSessionStorage` |
| Node.js script / CLI | `RelayerNode` (`@zama-fhe/sdk/node`) | `EthersSigner({ signer: wallet })` / `ViemSigner` | `memoryStorage` |
| Node.js server (concurrent requests) | `RelayerNode` | same | `asyncLocalStorage` (`@zama-fhe/sdk/node`) |
| Local Hardhat / cleartext | `RelayerCleartext` (`@zama-fhe/sdk/cleartext`) | any | `memoryStorage` |
| React Native / mobile | **not supported** — proxy via Node backend | | |

Network presets are values exported from `@zama-fhe/sdk`: `SepoliaConfig`, `MainnetConfig`, `HardhatConfig`. Spread them into the transports map and override `relayerUrl`/`network`:

```ts
transports: {
  [SepoliaConfig.chainId]: {
    ...SepoliaConfig,
    relayerUrl: "https://your-app.com/api/relayer/11155111", // browser: proxy via backend
    network: "https://sepolia.infura.io/v3/YOUR_KEY",
  },
}
```

## Universal gotchas

- **Package landscape.** Three `@zama-fhe/*` packages: `sdk` (core), `react-sdk` (hooks — requires `sdk` as a peer dep, install both explicitly), `relayer-sdk` (low-level, usually transitive). Import from `@zama-fhe/react-sdk` in React, from `@zama-fhe/sdk` elsewhere.
- **Sepolia needs no relayer proxy.** `SepoliaConfig.relayerUrl` already points at the public Zama testnet relayer. Spread `SepoliaConfig` as-is and leave `relayerUrl` alone. Only override it on mainnet.
- **Relayer API key (mainnet only).** The mainnet relayer needs an API key. Browser apps must proxy through their own backend (keep the key server-side). Node scripts pass `auth: { __type: "ApiKeyHeader", value: process.env.RELAYER_API_KEY }` directly.
- **COOP/COEP headers required for browser.** `RelayerWeb` uses a Web Worker with WASM + `SharedArrayBuffer`. Serve with `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`. Vite: `server.headers`. Next.js: `async headers()` in config.
- **Use the high-level token API for ERC-7984.** `sdk.createToken(addr)` returns a `Token` with `.shield`, `.balanceOf`, `.confidentialTransfer`, `.unshield`. Only drop to `useEncrypt`/`useUserDecrypt` for custom FHE contracts (auctions, voting, non-token).
- **Cleanup in Node.** Call `sdk.terminate()` on shutdown to stop worker threads.
- **Encrypt → ABI conversion.** `encrypt()` returns `handles: Uint8Array[]` and `inputProof: Uint8Array`. Wrap with viem `bytesToHex` (or `ethers.hexlify`) before passing to `writeContract` — ABIs expect `bytes32`/`bytes`.
- **Ciphertexts bind to one target contract.** The `contractAddress` in `encrypt()` must be the contract that will consume it. Encrypt per hop.

## Canonical doc paths

All paths are under `github.com/zama-ai/sdk/docs/gitbook/src/`:

- `tutorials/quick-start.md` — end-to-end setup for all 5 stacks
- `guides/configuration.md` — relayer + signer + storage deep dive
- `guides/authentication.md` — the backend proxy pattern for API keys
- `guides/node-js-backend.md` — worker pool + per-request isolation
- `guides/web-extensions.md` — MV3 with `chromeSessionStorage`
- `guides/local-development.md` — `RelayerCleartext` for Hardhat
- `guides/encrypt-decrypt.md` — low-level FHE for custom contracts
- `reference/sdk/ZamaSDK.md`, `reference/sdk/Token.md`, `reference/sdk/RelayerWeb.md`, `reference/sdk/RelayerNode.md`, `reference/sdk/network-presets.md`
- `reference/react/*.md` — every hook, one file each
