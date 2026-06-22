# Browser + viem setup

**Canonical doc:** `https://github.com/zama-ai/sdk/tree/main/docs/gitbook/src/tutorials/quick-start.md` (viem tab)

```bash
pnpm add @zama-fhe/sdk viem
```

The SDK config is assembled with `createConfig` from `@zama-fhe/sdk/viem` and wrapped
in `new ZamaSDK(...)`. `createConfig` builds the viem signer internally — you pass
native viem clients, a `web()` relayer transport per chain, and a storage backend.

```ts
import { createPublicClient, createWalletClient, custom, http } from "viem";
import { sepolia as viemSepolia } from "viem/chains";
import { ZamaSDK, indexedDBStorage } from "@zama-fhe/sdk";
import { sepolia, type FheChain } from "@zama-fhe/sdk/chains";
import { createConfig } from "@zama-fhe/sdk/viem";
import { web } from "@zama-fhe/sdk/web";

const [account] = await window.ethereum!.request({ method: "eth_requestAccounts" });
// createConfig builds a ViemSigner from this walletClient, so walletClient.account
// must be set — pass `account` here. Without it, signing/writes fail at call time
// with a wallet-not-connected error.
const publicClient = createPublicClient({ chain: viemSepolia, transport: http(RPC) });
const walletClient = createWalletClient({ account, chain: viemSepolia, transport: custom(window.ethereum!) });

// Spread the `sepolia` chain preset as-is — its relayerUrl already points at the
// public testnet relayer. Only override relayerUrl on mainnet, where you must proxy
// through your own backend to keep the API key server-side.
const zamaSepolia = { ...sepolia, network: RPC } as const satisfies FheChain;

const sdk = new ZamaSDK(
  createConfig({
    chains: [zamaSepolia],
    publicClient,
    walletClient,
    ethereum: window.ethereum,
    storage: indexedDBStorage,
    relayers: { [zamaSepolia.id]: web() },
  }),
);
```

## High-level token ops

`createToken` returns a `Token` (balance, transfer, operators). `shield` / `unshield`
/ `allowance` live on `WrappedToken` — get one with `createWrappedToken`.

```ts
// Balance, transfer, operators → Token
const token = sdk.createToken("0xYourConfidentialToken");
const balance = await token.balanceOf(account);
await token.confidentialTransfer("0xRecipient", 500n);

// Shield / unshield → WrappedToken
const wrapped = sdk.createWrappedToken("0xYourWrapper");
await wrapped.shield(1000n);
await wrapped.unshield(500n);
```

Vite needs COOP/COEP headers — see `../overview.md` Universal SDK gotchas.
