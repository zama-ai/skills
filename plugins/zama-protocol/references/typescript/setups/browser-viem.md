# Browser + viem setup

**Canonical doc:** `github.com/zama-ai/sdk/docs/gitbook/src/tutorials/quick-start.md` (viem tab)

```bash
pnpm add @zama-fhe/sdk viem
```

```ts
import { createPublicClient, createWalletClient, custom, http } from "viem";
import { sepolia } from "viem/chains";
import { ZamaSDK, RelayerWeb, SepoliaConfig, indexedDBStorage } from "@zama-fhe/sdk";
import { ViemSigner } from "@zama-fhe/sdk/viem";

const [account] = await window.ethereum!.request({ method: "eth_requestAccounts" });
// ViemSigner requires walletClient.account to be hoisted — pass `account` here,
// don't try to omit it. It will throw "WalletClient has no account" otherwise.
const publicClient = createPublicClient({ chain: sepolia, transport: http(RPC) });
const walletClient = createWalletClient({ account, chain: sepolia, transport: custom(window.ethereum!) });
const signer = new ViemSigner({ walletClient, publicClient, ethereum: window.ethereum });

// On Sepolia, spread SepoliaConfig as-is — its relayerUrl already points at
// the public testnet relayer. Only override relayerUrl on mainnet, where you
// must proxy through your own backend to keep the API key server-side.
const sdk = new ZamaSDK({
  relayer: new RelayerWeb({
    getChainId: () => signer.getChainId(),
    transports: {
      [SepoliaConfig.chainId]: { ...SepoliaConfig, network: RPC },
    },
  }),
  signer,
  storage: indexedDBStorage,
});
```

## High-level token ops

```ts
const token = sdk.createToken("0xYourEncryptedERC20");
await token.shield(1000n);
const balance = await token.balanceOf();
await token.confidentialTransfer("0xRecipient", 500n);
await token.unshield(500n);
```

Vite needs COOP/COEP headers — see `skill.md` → Universal gotchas.
