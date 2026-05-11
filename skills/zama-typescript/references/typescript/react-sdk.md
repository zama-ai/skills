# React SDK patterns

Use this note for `ZamaProvider`, storage choices, hook selection, and user-facing decrypt UX.

## Provider and storage

`ZamaProvider` needs a relayer, a signer, and a storage backend. Optional but important props include `sessionStorage`, `keypairTTL`, `sessionTTL`, and `onEvent`.

Create the signer first, then pass `getChainId: () => signer.getChainId()` into the relayer.

| Need | Storage |
|---|---|
| Normal browser persistence | `indexedDBStorage` |
| MV3 session signatures across worker restarts | `chromeSessionStorage` as `sessionStorage` |
| Tests or ephemeral state | `memoryStorage` |

If both `storage` and `sessionStorage` are persistent browser stores, keep them logically separate. Current React examples treat keypair storage and session-signature storage as separate concerns.

## Hook selection

- ERC-7984 token app: start from token hooks such as `useShield`, `useConfidentialBalance`, `useConfidentialTransfer`, `useUnshield`, and `useResumeUnshield`.
- Custom FHE contract: start from `useEncrypt`, `useUserDecrypt`, `useIsAllowed`, and `useAllow`.
- Delegated decrypt: use `useDelegateDecryption`, `useDelegationStatus`, `useDecryptBalanceAs`, or `useBatchDecryptBalancesAs`.
- Wrapper registry or discovery: use the registry/discovery hooks instead of hardcoding wrapper addresses.
- If unsure about exact hook names, check the **React reference** at `https://docs.zama.org/protocol/sdk` or inspect `node_modules/@zama-fhe/react-sdk/dist/esm/index.d.ts`.

## Decrypt UX

For decrypting reads, especially balances or custom decrypted results:

1. check `useIsAllowed({ contractAddresses })`
2. if false, show an explicit user action
3. call `useAllow`
4. enable the decrypting query or component only when allowed

This avoids blind signing on render and makes wallet prompts understandable.

Token example:

```tsx
const { data: allowed } = useIsAllowed({ contractAddresses: [tokenAddress] });
const { mutateAsync: allow } = useAllow();
const balance = useConfidentialBalance({ tokenAddress }, { enabled: !!allowed });
```

Custom-contract example:

```tsx
const { data: allowed } = useIsAllowed({ contractAddresses: [contractAddress] });
const { mutateAsync: allow } = useAllow();
const { data } = useUserDecrypt(
  { handles: resultHandle ? [{ handle: resultHandle, contractAddress }] : [] },
  { enabled: !!allowed && !!resultHandle },
);
```

If `allowed` is false, render a button that calls `allow([contractAddress])` instead of auto-triggering the decrypt flow.

## Pending unshield recovery

Unshield is a two-phase flow. If the page reloads after phase 1, the app must persist the unwrap tx hash itself:

- `savePendingUnshield(storage, wrapperAddress, unwrapTxHash)`
- `loadPendingUnshield(storage, wrapperAddress)`
- `clearPendingUnshield(storage, wrapperAddress)`
- `useResumeUnshield({ tokenAddress })`

The common pattern is: save the phase-1 tx hash, load pending state on mount, show a resume action, and clear state after finalize succeeds.

## Avoid

- calling `useAllow` automatically on render
- firing decrypt queries before checking `useIsAllowed`
- using `useRevokeSession` as normal post-operation cleanup
- presenting session teardown as the default way to respect `sessionTTL`

Use `useRevokeSession` for explicit teardown only: sign out, disconnect, security reset, or "forget this device/session".
