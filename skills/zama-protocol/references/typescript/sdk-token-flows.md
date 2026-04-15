# SDK token flows (ERC-7984 and wrappers)

Use this note for SDK integration with ERC-7984 tokens and ERC20 wrappers: shield, confidential balance, confidential transfer, unshield, delegated balance reads, and wrapper discovery.

Do not use this note for custom FHE contracts such as voting or auctions; use `sdk-custom-contract-flows.md`.

## First principle: wrappers and confidential tokens

There are two token addresses in wrapper flows:

- underlying ERC20 token
- confidential ERC-7984 wrapper token

Do not hardcode this mapping unless the app owns deployment. Prefer wrapper discovery or registry helpers when available.

## Core token operations

### 1. Shield

Shielding moves public ERC20 into confidential ERC-7984 balance.

Typical sequence:

1. approve the wrapper to spend underlying ERC20
2. call SDK token `.shield(...)` or React `useShield`
3. wait for the transaction
4. read confidential balance only after session authorization

### 2. Read confidential balance

This is a decrypting read, so session authorization matters. Pair it with `sdk-permissions-and-sessions.md` or `react-sdk.md`.

React pattern:

- `useIsAllowed({ contractAddresses: [tokenAddress] })`
- if false, show an unlock button using `useAllow`
- pass `{ enabled: !!allowed }` to `useConfidentialBalance`

### 3. Confidential transfer

Use high-level token helpers:

- Core SDK: `token.confidentialTransfer(...)`
- React SDK: `useConfidentialTransfer`

Avoid hand-rolling encrypted transfer calldata unless the token API cannot express the target flow.

### 4. Unshield

Unshielding is a two-phase flow:

1. request unwrap / burn confidential amount
2. finalize unwrap after the proof/event path completes

React apps must handle interrupted flows; see `react-sdk.md` for pending-unshield persistence.

### 5. Resume interrupted unshield

Use:

- `useResumeUnshield({ tokenAddress })`
- `savePendingUnshield`
- `loadPendingUnshield`
- `clearPendingUnshield`

Persist the unwrap tx hash when phase 1 is submitted. Do not assume the browser stays open until finalize.

## Delegation on token flows

Use delegated decrypt when a portfolio view, backend, or authorized third party needs to decrypt balances for a user:

- `delegateDecryption`
- `delegationStatus`
- `decryptBalanceAs`
- `batchDecryptBalancesAs`

Keep this separate from operator approvals. Operator approvals let someone transfer; decrypt delegation lets someone read.

## What not to do

- Do not reimplement ERC-7984 encrypted balance logic in app contracts.
- Do not treat wrapper and underlying token addresses as interchangeable.
- Do not trigger wallet decrypt signatures on render.
- Do not revoke the whole session after every balance read.
- Do not use token hooks for custom FHE contracts.

## Related

- `sdk-permissions-and-sessions.md`
- `react-sdk.md`
- `sdk-custom-contract-flows.md`
