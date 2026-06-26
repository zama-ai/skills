# SDK token flows (ERC-7984 and wrappers)

Use this note for SDK integration with ERC-7984 tokens and ERC20 wrappers: shield, confidential balance, confidential transfer, unshield, delegated balance reads, and wrapper discovery.

Do not use this note for custom FHE contracts such as voting or auctions; use `custom-contracts.md`.

## First principle: wrappers and confidential tokens

There are two token addresses in wrapper flows:

- underlying ERC20 token
- confidential ERC-7984 wrapper token

Do not hardcode this mapping unless the app owns deployment. Prefer wrapper discovery or registry helpers when available (`sdk.registry.getConfidentialToken(erc20)`).

## Token vs WrappedToken

Two core-SDK factories:

- `sdk.createToken(address)` → `Token` — balance, `confidentialTransfer`, operators, decryption.
- `sdk.createWrappedToken(address)` → `WrappedToken` (extends `Token`) — adds `shield`, `unshield`, `unshieldAll`, `approveUnderlying`, `allowance`, `unwrap*`, `finalizeUnwrap`.

Use `createWrappedToken` whenever you shield/unshield; `createToken` is enough for read/transfer.

## Core token operations

Write methods (`shield`, `unshield`, `confidentialTransfer`, `setOperator`, …) resolve to a `TransactionResult` — read `.txHash` (a `Hex`) and `.receipt` (the mined receipt), **not** `.hash`. The route `shield` took (`transferAndCall` vs `approveAndWrap`) is not on the return value; it is reported as `shieldPath` on the `ShieldSubmitted` event via the `onEvent` callback.

### 1. Shield

Shielding moves public ERC20 into confidential ERC-7984 balance. `WrappedToken.shield` (or `useShield`) handles the routing — it detects ERC-1363 support and routes through `transferAndCall` (one tx) or `approve` + `wrap` (two txs) automatically. Don't compose the approve/wrap calls by hand.

Typical sequence:

1. call `sdk.createWrappedToken(wrapper).shield(amount)` or React `useShield`
2. wait for the transaction
3. read confidential balance only after a decrypt permit is granted

### 2. Read confidential balance

This is a decrypting read, so a permit matters. Pair it with `permissions.md` or `react.md`.

`token.balanceOf(owner)` decrypts via **your own** permit — it is the read-your-own-balance path. To read **another** account's balance, that account must first grant you a decrypt delegation; you then call `Token.decryptBalanceAs({ delegatorAddress })` (see *Delegation on token flows* below).

React pattern:

- `useHasPermit({ contractAddresses: [tokenAddress] })`
- if false, show an unlock button using `useGrantPermit`
- pass `{ enabled: !!hasPermit }` to `useConfidentialBalance({ address: tokenAddress, account })`

### 3. Confidential transfer

Use high-level token helpers:

- Core SDK: `token.confidentialTransfer(...)`
- React SDK: `useConfidentialTransfer`

Avoid hand-rolling encrypted transfer calldata unless the token API cannot express the target flow.

### 4. Unshield

Unshielding is a two-phase flow:

1. request unwrap / burn confidential amount
2. finalize unwrap after the proof/event path completes

React apps must handle interrupted flows; see `react.md` for pending-unshield persistence.

### 5. Resume interrupted unshield

Use:

- `useResumeUnshield(wrapperAddress)` — the wrapper address is a positional argument
- `savePendingUnshield(storage, wrapperAddress, unwrapTxHash)`
- `loadPendingUnshield(storage, wrapperAddress)`
- `clearPendingUnshield(storage, wrapperAddress)`

Persist the unwrap tx hash when phase 1 is submitted (the robust trigger is `onEvent` watching `ZamaSDKEvents.UnshieldPhase1Submitted`). Do not assume the browser stays open until finalize.

## Operators (not approvals)

ERC-7984 authorizes third-party transfers with an **operator** model — there is no ERC20-style `approve` / `allowance` / `isApproved` on the confidential token. An operator may move the holder's confidential balance until an optional expiry.

- `token.setOperator(operator, until?)` — `until` is a Unix-seconds expiry; omit for none.
- `token.isOperator(holder, spender)` — **holder first**, then the operator address. Easy to reverse.
- React: `useConfidentialSetOperator(tokenAddress)` (positional) and `useConfidentialIsOperator({ address, holder, spender })`.

Do not confuse this with `approveUnderlying` / `useApproveUnderlying` — that is the ERC20 approval on the *underlying* token ahead of a shield, not a confidential-token operator.

## Delegation on token flows

Use delegated decrypt when a portfolio view, backend, or authorized third party needs to decrypt balances for a user:

- Core SDK: `sdk.delegations.delegateDecryption`, `sdk.delegations.revokeDelegation`, `sdk.delegations.isActive`, `sdk.delegations.getExpiry`; `Token.decryptBalanceAs` / `Token.batchDecryptBalancesAs`
- React hooks: `useDelegateDecryption`, `useDelegationStatus`, `useDecryptBalanceAs`, `useBatchDecryptBalancesAs`

Keep this separate from operator approvals. Operator approvals let someone transfer; decrypt delegation lets someone read.

## What not to do

- Do not reimplement ERC-7984 encrypted balance logic in app contracts.
- Do not treat wrapper and underlying token addresses as interchangeable.
- Do not trigger wallet decrypt signatures on render.
- Do not clear credentials after every balance read.
- Do not use token hooks for custom FHE contracts.

## Related

- `permissions.md`
- `react.md`
- `custom-contracts.md`
