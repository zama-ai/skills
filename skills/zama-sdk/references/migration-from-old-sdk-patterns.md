# Migration from Older SDK Patterns

Use this note when the target codebase already contains older relayer or fhevm integration code.

## Recognition Heuristics

Look for signs such as:

- custom relayer bootstrap code not centered on `ZamaSDK`
- direct decrypt authorization orchestration
- custom wrapper discovery logic
- token flows implemented as ad hoc contract interactions instead of SDK token methods

## Migration Order

1. Replace old bootstrap code with explicit `relayer + signer + storage`.
2. Instantiate `ZamaSDK`.
3. Replace old token operations with:
   - `shield()`
   - `confidentialTransfer()`
   - `unshield()`
   - `balanceOf()`
4. Replace old decrypt authorization code with:
   - `allow()`
   - `revoke()`
   - `isAllowed()`
5. Replace old delegated decrypt code with:
   - `delegateDecryption()`
   - `revokeDelegation()`
   - `decryptBalanceAs()`

## Old to New Mapping

- custom relayer bootstrap -> `new ZamaSDK({ relayer, signer, storage })`
- manual credential lifecycle -> `allow()` / `revoke()` / `isAllowed()`
- custom wrapper address lookup -> registry APIs or `discoverWrapper()`
- custom confidential writes -> `shield()` / `confidentialTransfer()` / `unshield()`
- custom delegated reads -> `delegateDecryption()` / `decryptBalanceAs()` / `revokeDelegation()`

## Do Not

- do a blind rename-only migration
- keep old credential lifecycle code when the current SDK already owns it
- keep bespoke wrapper assumptions if registry discovery exists
