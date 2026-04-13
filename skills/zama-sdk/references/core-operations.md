# Core Operations

## Main Token Flow

Use this order:

1. resolve or discover the wrapper
2. `shield()`
3. `confidentialTransfer()`
4. `balanceOf()`
5. `unshield()`

## Example

```ts
const sdk = new ZamaSDK({ relayer, signer, storage });
const token = sdk.createToken("0xEncryptedERC20");

await token.shield(1000n);
await token.confidentialTransfer("0xRecipient", 250n);
const balance = await token.balanceOf();
await token.unshield(100n);
```

## Balance Reads

- Use `balanceOf()` for the normal decrypt flow.
- Use `ReadonlyToken.allow(...)` to pre-authorize multiple tokens at once without a full token context. Prefer this for batch portfolio reads across multiple addresses.
- Distinguish `NoCiphertextError` from a decrypted `0n` balance.

## Batch Reads

Use batch APIs when the app needs portfolio-style reads across multiple tokens.
