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

- `setups/react-wagmi.md` - React app using `@zama-fhe/react-sdk` with wagmi UI state and `ViemSigner`
- `setups/browser-viem.md` - browser app using `@zama-fhe/sdk` with viem
- `setups/browser-ethers.md` - browser app using `@zama-fhe/sdk` with ethers
- `setups/node-backend.md` - Node.js scripts, servers, workers, and custom signer backends
- `setups/extension-mv3.md` - MV3 extension with persistent session signatures
- `setups/localhost-setup.md` - cleartext mode for local Hardhat, Hoodi, or other unsupported-chain testing

## Mental model

```text
ZamaSDK <- Relayer  (FHE backend - runs encrypt/decrypt in a worker)
        <- Signer   (wallet - getChainId, signTypedData, writeContract)
        <- Storage  (FHE keypair cache; sessionStorage caches wallet sig)
```

Instantiate the signer first, then pass `getChainId: () => signer.getChainId()` into the relayer. The relayer switches FHE workers automatically when the chain changes.

## Environment matrix

| Environment | Relayer | Signer | Storage |
|---|---|---|---|
| React + wagmi | `RelayerWeb` | `ViemSigner` (`@zama-fhe/sdk/viem`) | `indexedDBStorage` |
| Browser + viem | `RelayerWeb` | `ViemSigner` (`@zama-fhe/sdk/viem`) | `indexedDBStorage` |
| Browser + ethers | `RelayerWeb` | `EthersSigner({ ethereum: window.ethereum })` | `indexedDBStorage` |
| MV3 extension | `RelayerWeb` | `ViemSigner` / `EthersSigner` | `storage: indexedDBStorage`, `sessionStorage: chromeSessionStorage` |
| Node.js script / CLI | `RelayerNode` (`@zama-fhe/sdk/node`) | `EthersSigner({ signer: wallet })` / `ViemSigner` | `memoryStorage` |
| Node.js server (concurrent requests) | `RelayerNode` | same | `asyncLocalStorage` (`@zama-fhe/sdk/node`) |
| Local Hardhat / cleartext | `RelayerCleartext` (`@zama-fhe/sdk/cleartext`) | any | `memoryStorage` |
| React Native / mobile | Not supported - proxy via Node backend | | |

Do not use `WagmiSigner` from `@zama-fhe/react-sdk/wagmi` until its upstream bundling issue is fixed. It imports `watchConnection` from `wagmi/actions`, which breaks real bundlers even when typecheck passes.

Network presets are values exported from `@zama-fhe/sdk`: `SepoliaConfig`, `MainnetConfig`, `HardhatConfig`. Spread them into the transports map and override `relayerUrl` or `network` as needed:

```ts
transports: {
  [SepoliaConfig.chainId]: {
    ...SepoliaConfig,
    relayerUrl: "https://your-app.com/api/relayer/11155111", // browser: proxy via backend
    network: "https://sepolia.infura.io/v3/YOUR_KEY",
  },
}
```

## Choose one task reference

| Need | Read |
|---|---|
| Package overview, sub-paths, signer choice, `GenericSigner` | `packages-and-signers.md` |
| ERC-7984 token integration: shield, transfer, balance, unshield, wrapper discovery | `tokens.md` |
| Custom FHE contracts: encrypt input, read handles, decrypt output | `custom-contracts.md` |
| Session signatures, `useAllow`, `useRevoke`, delegation, TTLs | `permissions.md` |
| React provider, storage, hook selection, decrypt UX | `react.md` |
| Migrating older SDK / relayer / FHEVM-style integrations | `packages-and-signers.md` |

## Universal gotchas

- **Package landscape.** Install `@zama-fhe/sdk` explicitly. `@zama-fhe/react-sdk` requires it as a peer dependency and pnpm will not install peers automatically.
- **Sepolia needs no relayer proxy.** `SepoliaConfig.relayerUrl` already points at the public Zama testnet relayer. Spread `SepoliaConfig` as-is and leave `relayerUrl` alone. Only override it on mainnet.
- **Relayer API key (mainnet only).** Browser apps must proxy mainnet relayer requests through their own backend to keep the API key server-side. Node scripts pass `auth: { __type: "ApiKeyHeader", value: process.env.RELAYER_API_KEY }` directly (note the **double-underscore** `__type` — that's the discriminator the relayer-sdk type expects).
- **COOP/COEP headers required for browser.** `RelayerWeb` uses a Web Worker with WASM + `SharedArrayBuffer`. Serve with `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`. Vite: `server.headers`. Next.js: `async headers()` in config.
- **Use the high-level token API for ERC-7984.** `sdk.createToken(addr)` returns a `Token` with `.shield`, `.balanceOf`, `.confidentialTransfer`, `.unshield`. Use `useEncrypt` / `useUserDecrypt` for custom FHE contracts such as auctions and voting.
- **Encrypt -> ABI conversion.** `encrypt()` returns `handles: Uint8Array[]` and `inputProof: Uint8Array`. Wrap with viem `bytesToHex` or `ethers.hexlify` before passing to contract calls; ABIs expect `bytes32` or `bytes`.
- **Ciphertexts bind to one target contract.** The `contractAddress` in `encrypt()` must be the contract that will consume it. Encrypt per hop.
- **Do not treat the SDK as token-only.** Token helpers are the happy path for ERC-7984, but the same stack also supports custom FHE contracts. Route those cases to `custom-contracts.md`.

## Canonical doc paths

Hosted at `https://docs.zama.org/protocol/sdk`:

- **Tutorials** — Quick start · First confidential dApp · Wallet & exchange integration
- **Guides** — Configuration · Authentication · Relayer API keys · Shield · Transfer privately · Unshield · Check balances · Handle errors · Activity feeds · Node.js backend · Web extensions · Local development · Next.js SSR · Operator approvals · Encrypt & decrypt
- **API reference (SDK)** — `ZamaSDK`, `Token`, `ReadonlyToken`, `WrappersRegistry`, `RelayerWeb`, `RelayerNode`, `RelayerCleartext`, `ViemSigner`, `EthersSigner`, `WagmiSigner`, `GenericSigner`, `GenericStorage`, network presets, errors, contract builders, event decoders, delegated decryption
- **API reference (React)** — `ZamaProvider` + the full hook surface (`useShield`, `useConfidentialBalance(s)`, `useConfidentialTransfer(From)`, `useUnshield(All)`, `useResumeUnshield`, `useUnwrap(All)`, `useFinalizeUnwrap`, `useAllow`, `useIsAllowed`, `useRevoke`, `useRevokeSession`, `useConfidentialApprove`, `useEncrypt`, `useUserDecrypt`, `usePublicDecrypt`, `useDelegateDecryption`, `useRevokeDelegation`, `useDelegationStatus`, `useDecryptBalanceAs`, `useBatchDecryptBalancesAs`, plus wrapper-registry / discovery hooks)
