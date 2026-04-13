# Setup and Subpaths

## Main Package Choices

- `@zama-fhe/sdk` for core runtime-agnostic APIs
- `@zama-fhe/sdk/node` for Node-specific runtime features
- `@zama-fhe/sdk/viem` for `ViemSigner`
- `@zama-fhe/sdk/ethers` for `EthersSigner`
- `@zama-fhe/sdk/cleartext` for `RelayerCleartext`

## Runtime Rules

- Node.js: `RelayerNode`
- Local or approved cleartext test flows: `RelayerCleartext`
- If the target is a React app, use `zama-react-sdk` instead of this skill.

## Minimal Node Example

```ts
import { ZamaSDK, SepoliaConfig, memoryStorage } from "@zama-fhe/sdk";
import { RelayerNode } from "@zama-fhe/sdk/node";
import { ViemSigner } from "@zama-fhe/sdk/viem";

const signer = new ViemSigner({ walletClient, publicClient });

const sdk = new ZamaSDK({
  relayer: new RelayerNode({
    getChainId: () => signer.getChainId(),
    transports: {
      [SepoliaConfig.chainId]: {
        ...SepoliaConfig,
        network: process.env.RPC_URL!,
        auth: { __type: "ApiKeyHeader", value: process.env.RELAYER_API_KEY! },
      },
    },
  }),
  signer,
  storage: memoryStorage,
});
```

## Minimal Cleartext Example

```ts
import { ZamaSDK, memoryStorage } from "@zama-fhe/sdk";
import { RelayerCleartext, hoodiCleartextConfig } from "@zama-fhe/sdk/cleartext";

const relayer = new RelayerCleartext({
  ...hoodiCleartextConfig,
  network: process.env.HOODI_RPC_URL!,
});

const sdk = new ZamaSDK({
  relayer,
  signer,
  storage: memoryStorage,
});
```
