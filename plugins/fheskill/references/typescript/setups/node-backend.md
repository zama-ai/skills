# Node.js backend setup

**Canonical doc:** `github.com/zama-ai/sdk/docs/gitbook/src/guides/node-js-backend.md`

Also the pattern for **React Native / mobile**: expose `/encrypt` and `/user-decrypt` HTTP endpoints and forward from the app.

```bash
pnpm add @zama-fhe/sdk ethers
# or: pnpm add @zama-fhe/sdk viem
```

## Script / single-user CLI

```ts
import { ZamaSDK, SepoliaConfig, memoryStorage } from "@zama-fhe/sdk";
import { RelayerNode } from "@zama-fhe/sdk/node";
import { EthersSigner } from "@zama-fhe/sdk/ethers";
import { JsonRpcProvider, Wallet } from "ethers";

const wallet = new Wallet(process.env.PRIVATE_KEY!, new JsonRpcProvider(process.env.RPC_URL));
const signer = new EthersSigner({ signer: wallet }); // node takes `signer`, browser takes `ethereum`

const sdk = new ZamaSDK({
  relayer: new RelayerNode({
    getChainId: () => signer.getChainId(),
    poolSize: 4, // defaults to min(CPU cores, 4)
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

try {
  const token = sdk.createToken("0xToken");
  await token.confidentialTransfer("0xRecipient", 500n);
} finally {
  sdk.terminate(); // stops worker threads
}
```

## Server with concurrent requests

Use `asyncLocalStorage` from `@zama-fhe/sdk/node` to isolate the FHE keypair per request. Wrap each handler in `asyncLocalStorage.run(...)`:

```ts
import { asyncLocalStorage } from "@zama-fhe/sdk/node";

app.post("/api/transfer", (req, res) => {
  asyncLocalStorage.run(async () => {
    const sdk = new ZamaSDK({ relayer, signer, storage: asyncLocalStorage });
    await sdk.createToken(TOKEN).confidentialTransfer(req.body.to, BigInt(req.body.amount));
    res.json({ ok: true });
  });
});
```

See `guides/node-js-backend.md` for the full per-request isolation pattern.
