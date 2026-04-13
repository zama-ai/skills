# Delegation and Credentials

## Credentials

Use:

- `allow()` to authorize decrypts
- `revoke()` to clear authorization
- `isAllowed()` to check current session state

Keep these rules in mind:

- `sessionTTL` is explicit product behavior
- do not set `sessionTTL` above one year
- respect the 10-contract credential limit

## Delegation

Use:

- `delegateDecryption()`
- `revokeDelegation()`
- `decryptBalanceAs()`

Use delegation only when the product needs delegated balance visibility.

## Minimal Shape

```ts
const allowed = await token.isAllowed();
if (!allowed) await token.allow();

await token.delegateDecryption({ delegateAddress });
const balance = await token.decryptBalanceAs({ delegatorAddress });
await token.revokeDelegation({ delegateAddress });
```

## Session Guidance

- scripts can use `memoryStorage` (from `@zama-fhe/sdk`)
- multi-user servers should use `asyncLocalStorage` (from `@zama-fhe/sdk/node`)
- keep credential state scoped to the user or request context
