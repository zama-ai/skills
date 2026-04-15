# Browser + ethers setup

**Canonical doc:** `https://github.com/zama-ai/sdk/tree/main/docs/gitbook/src/tutorials/quick-start.md` (ethers tab)

```bash
pnpm add @zama-fhe/sdk ethers
```

`EthersSigner` in the browser takes the **raw EIP-1193 provider**, not an `ethers.Wallet`:

```ts
import { ZamaSDK, RelayerWeb, SepoliaConfig, indexedDBStorage } from "@zama-fhe/sdk";
import { EthersSigner } from "@zama-fhe/sdk/ethers";

const signer = new EthersSigner({ ethereum: window.ethereum! });

const sdk = new ZamaSDK({
  relayer: new RelayerWeb({
    getChainId: () => signer.getChainId(),
    transports: {
      // Sepolia: spread SepoliaConfig as-is. Its relayerUrl already points at
      // the public testnet relayer. Only override on mainnet (proxy the API key).
      [SepoliaConfig.chainId]: { ...SepoliaConfig, network: RPC },
    },
  }),
  signer,
  storage: indexedDBStorage,
});

const token = sdk.createToken("0xYourEncryptedERC20");
await token.shield(1000n);
await token.confidentialTransfer("0xRecipient", 500n);
```

Needs COOP/COEP headers - see `../typescript.md` Universal SDK gotchas.
