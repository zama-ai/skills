# Localhost — Cleartext setup

**Canonical doc:** `https://github.com/zama-ai/sdk/tree/main/docs/gitbook/src/guides/local-development.md`

For local nodes and custom testnets running in **cleartext mode** — values are stored as plaintext on-chain, no KMS, no gateway, no WASM. The only change vs. a real deployment is the relayer transport: swap `web()` / `node()` for **`cleartext()`**. The rest of your code is unchanged.

Blocked on Ethereum Mainnet and Sepolia — dev/test only.

```ts
import { ZamaSDK, MemoryStorage, cleartext } from "@zama-fhe/sdk";
import { hardhat, type FheChain } from "@zama-fhe/sdk/chains";
import { createConfig } from "@zama-fhe/sdk/ethers";
import { JsonRpcProvider, Wallet } from "ethers";

const wallet = new Wallet(PRIVATE_KEY, new JsonRpcProvider("http://127.0.0.1:8545"));
const localChain = { ...hardhat, network: "http://127.0.0.1:8545" } as const satisfies FheChain;

const sdk = new ZamaSDK(
  createConfig({
    chains: [localChain],
    signer: wallet,
    storage: new MemoryStorage(),
    relayers: { [localChain.id]: cleartext() }, // ← cleartext transport, no relayer/KMS network
  }),
);

const wrapped = sdk.createWrappedToken("0xYourWrapper");
await wrapped.shield(1000n);
```

For the hosted cleartext testnets, use the built-in chain presets instead of `hardhat`:
`hoodi`, `ingenTestnet`, and `bscTestnet` from `@zama-fhe/sdk/chains` (each already carries its `registryAddress`). The `cleartext` factory is also re-exported from `@zama-fhe/sdk/node`.

Runnable cleartext examples live in the SDK repo: `examples/example-ingen` and `examples/example-hoodi`.
