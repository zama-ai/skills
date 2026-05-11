# Localhost - Cleartext setup

**Canonical doc:** `https://github.com/zama-ai/sdk/tree/main/docs/gitbook/src/guides/local-development.md`

For local Hardhat nodes and custom testnets deployed in **cleartext mode** — values are stored as plaintext on-chain, no KMS, no gateway, no WASM. Drop-in replacement for `RelayerWeb`/`RelayerNode`; the rest of your code is unchanged.

Blocked on Ethereum Mainnet and Sepolia — dev/test only.

```ts
import { ZamaSDK, memoryStorage } from "@zama-fhe/sdk";
import { RelayerCleartext, hardhatCleartextConfig } from "@zama-fhe/sdk/cleartext";
import { ViemSigner } from "@zama-fhe/sdk/viem";

const relayer = new RelayerCleartext(hardhatCleartextConfig);
// Or for the Hoodi cleartext testnet:
// import { hoodiCleartextConfig } from "@zama-fhe/sdk/cleartext";
// const relayer = new RelayerCleartext(hoodiCleartextConfig);

const sdk = new ZamaSDK({ relayer, signer, storage: memoryStorage });

const token = sdk.createToken("0xYourToken");
await token.shield(1000n);
```

Example implementation of cleartext setup is in https://github.com/zama-ai/fhevm-react-template