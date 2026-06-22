# React SDK patterns

Use this note for `ZamaProvider`, storage choices, hook selection, and user-facing decrypt UX.

## Provider and storage

`ZamaProvider` takes a single **`config`** prop — a `ZamaConfig` built with `createConfig` (from `@zama-fhe/sdk/viem`, `@zama-fhe/sdk/ethers`, or `@zama-fhe/react-sdk/wagmi`):

```tsx
<ZamaProvider config={zamaConfig}>{children}</ZamaProvider>
```

`createConfig` takes `chains`, a `relayers` map (`web()` per chain in the browser), `storage`, and optionally `permitStorage`, `permitTTL`, `transportKeyPairTTL`, `registryTTL`, and `onEvent`. The signer/provider are built inside `createConfig` — there is no separate signer prop and no `getChainId` wiring. See `setups/react-wagmi.md` for a full provider.

| Need | Storage |
|---|---|
| Normal browser persistence | `indexedDBStorage` |
| MV3 permit credential across worker restarts | `chromeSessionStorage` as `permitStorage` |
| Tests or ephemeral state | `memoryStorage` |

`storage` (encrypted FHE keypair) and `permitStorage` (the wallet-signed permit) should be **separate** instances when both are persistent browser stores — sharing one corrupts the cached credentials. `permitStorage` defaults to `storage` when omitted.

## Hook selection

- ERC-7984 token app: start from token hooks such as `useShield`, `useConfidentialBalance`, `useConfidentialTransfer`, `useUnshield`, and `useResumeUnshield`.
- Custom FHE contract: start from `useEncrypt`, `useDecryptValues`, `useHasPermit`, and `useGrantPermit`.
- Delegated decrypt: use `useDelegateDecryption`, `useDelegationStatus`, `useDecryptBalanceAs`, or `useBatchDecryptBalancesAs`.
- Wrapper registry or discovery: use the registry/discovery hooks (`useListPairs`, `useWrapperDiscovery`, …) instead of hardcoding wrapper addresses.
- If unsure about exact hook names, check the **React reference** at `https://docs.zama.org/protocol/sdk` or inspect `node_modules/@zama-fhe/react-sdk/dist/esm/index.d.ts`.

## Decrypt UX

For decrypting reads, especially balances or custom decrypted results:

1. check `useHasPermit({ contractAddresses })`
2. if false, show an explicit user action
3. call `useGrantPermit`
4. enable the decrypting query or component only when the permit is present

This avoids blind signing on render and makes wallet prompts understandable.

Token example:

```tsx
// tokenAddress is your app's; account comes from the wallet (e.g. wagmi `useAccount`)
const { data: hasPermit } = useHasPermit({ contractAddresses: [tokenAddress] });
const { mutateAsync: grantPermit } = useGrantPermit();
const balance = useConfidentialBalance({ address: tokenAddress, account }, { enabled: !!hasPermit });
```

Custom-contract example (`useDecryptValues` takes the `EncryptedInput[]` array directly):

```tsx
const { data: hasPermit } = useHasPermit({ contractAddresses: [contractAddress] });
const { mutateAsync: grantPermit } = useGrantPermit();
const { data } = useDecryptValues(
  resultHandle ? [{ encryptedValue: resultHandle, contractAddress }] : [],
  { enabled: !!hasPermit && !!resultHandle },
);
```

If `hasPermit` is false, render a button that calls `grantPermit([contractAddress])` instead of auto-triggering the decrypt flow.

## Pending unshield recovery

Unshield is a two-phase flow. If the page reloads after phase 1, the app must persist the unwrap tx hash itself. The robust trigger is `onEvent` on the config — watch `ZamaSDKEvents.UnshieldPhase1Submitted` (the SDK awaits the receipt before emitting) and save then:

- `savePendingUnshield(storage, wrapperAddress, unwrapTxHash)`
- `loadPendingUnshield(storage, wrapperAddress)`
- `clearPendingUnshield(storage, wrapperAddress)`
- `useResumeUnshield(wrapperAddress)` — the wrapper address is a positional argument

The common pattern is: save the phase-1 tx hash (via `onEvent`), load pending state on mount, show a resume action, and clear state after finalize succeeds.

## Avoid

- calling `useGrantPermit` automatically on render
- firing decrypt queries before checking `useHasPermit`
- using `useClearCredentials` as normal post-operation cleanup
- presenting credential teardown as the default way to respect `permitTTL`

Use `useClearCredentials` for explicit teardown only: sign out, disconnect, security reset, or "forget this device/session".
