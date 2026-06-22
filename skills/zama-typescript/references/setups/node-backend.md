# Node.js backend setup

**Canonical doc:** `https://github.com/zama-ai/sdk/tree/main/docs/gitbook/src/guides/node-js-backend.md`

Also the pattern for **React Native / mobile**: expose `/encrypt` and `/decrypt` HTTP endpoints and forward from the app.

```bash
pnpm add @zama-fhe/sdk ethers
# or: pnpm add @zama-fhe/sdk viem
```

## Script / single-user CLI

In Node, use the `node()` relayer transport (a worker pool) and pass the wallet via
`createConfig`. With ethers, `createConfig` from `@zama-fhe/sdk/ethers` takes
`signer: wallet` (an ethers `Wallet` with an attached provider); the browser case
takes `ethereum` instead. The relayer API key goes on the chain preset's `auth` field.

```ts
import { ZamaSDK, MemoryStorage } from "@zama-fhe/sdk";
import { sepolia, type FheChain } from "@zama-fhe/sdk/chains";
import { createConfig } from "@zama-fhe/sdk/ethers";
import { node } from "@zama-fhe/sdk/node";
import { JsonRpcProvider, Wallet } from "ethers";

const wallet = new Wallet(process.env.PRIVATE_KEY!, new JsonRpcProvider(process.env.RPC_URL));

const zamaSepolia = {
  ...sepolia,
  network: process.env.RPC_URL!,
  auth: { __type: "ApiKeyHeader", value: process.env.RELAYER_API_KEY! },
} as const satisfies FheChain;

const sdk = new ZamaSDK(
  createConfig({
    chains: [zamaSepolia],
    signer: wallet, // node: ethers Wallet with provider; browser would pass `ethereum`
    storage: new MemoryStorage(),
    relayers: { [zamaSepolia.id]: node() }, // node() accepts { poolSize } — defaults to min(CPU cores, 4)
  }),
);

const token = sdk.createToken("0xConfidentialToken");
await token.confidentialTransfer("0xRecipient", 500n);
```

(viem in Node: import `createConfig` from `@zama-fhe/sdk/viem` and pass
`publicClient` + `walletClient` instead of `signer`.)

## Relayer auth scheme

The `auth` scheme must match where the relayer lives — the wrong one is rejected:

| `auth.__type` | Sent as | Use against |
|---|---|---|
| `ApiKeyHeader` (`value`) | `x-api-key` header | **Zama-hosted relayer — required.** It accepts the key only here; also the default. |
| `ApiKeyCookie` (`value`) | `x-api-key` cookie | Your own proxy — authenticate the SDK→proxy hop; the proxy then injects `x-api-key` upstream. |
| `BearerToken` (`token`) | `Authorization: Bearer` | A **self-hosted** relayer whose auth layer expects a bearer token. |

Against the Zama-hosted relayer only `ApiKeyHeader` works — do not reach for `BearerToken`. Note the field name differs: `ApiKeyHeader` / `ApiKeyCookie` carry the key in `value`, `BearerToken` in `token`.

## Server with concurrent requests

Use `asyncLocalStorage` from `@zama-fhe/sdk/node` to isolate the FHE credentials per
request. Build the SDK inside `asyncLocalStorage.run(...)` so each handler gets its own
storage context:

```ts
import { asyncLocalStorage } from "@zama-fhe/sdk/node";

// Reuses `wallet` and `zamaSepolia` from above; only `storage` is per-request.
app.post("/api/transfer", (req, res) => {
  asyncLocalStorage.run(async () => {
    const sdk = new ZamaSDK(
      createConfig({
        chains: [zamaSepolia],
        signer: wallet,
        storage: asyncLocalStorage,
        relayers: { [zamaSepolia.id]: node() },
      }),
    );
    await sdk.createToken(TOKEN).confidentialTransfer(req.body.to, BigInt(req.body.amount));
    res.json({ ok: true });
  });
});
```

Use the `cleartext()` transport instead of `node()` only for local dev or chains where
Zama Protocol has not deployed the full listener/relayer stack yet (see `localhost-setup.md`).

Next read:

- `../packages-and-signers.md`
- `../tokens.md`
- `../custom-contracts.md`
