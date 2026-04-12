# Advanced FHE Reference

Read this when you go beyond `ERC7984`'s built-in confidential transfer / mint / burn — i.e. when you write FHE arithmetic or comparisons yourself, manage ACL by hand, or do production decryption.

If all you're doing is `_mint` / `_burn` / `confidentialTransfer` on `ERC7984`, you do NOT need this file — `ERC7984` handles ACL and arithmetic internally.

## ACL (Access Control List)

The ACL controls who can access encrypted handles. After you create or compute an encrypted value, grant permissions:

```solidity
euint64 value = FHE.fromExternal(input, proof);
FHE.allowThis(value);              // contract may use it later

euint64 result = FHE.add(existing, value);
FHE.allowThis(result);             // required to store
FHE.allow(result, msg.sender);     // grant to user
```

| Function | Purpose |
|---|---|
| `FHE.allowThis(handle)` | Persistent permission for current contract |
| `FHE.allow(handle, address)` | Persistent permission for an address |
| `FHE.allowTransient(handle, address)` | Temporary (current tx only) |
| `FHE.isAllowed(handle, address)` | Check |
| `FHE.isSenderAllowed(handle)` | Check `msg.sender` |
| `FHE.isInitialized(handle)` | Check init |

### User decryption delegation

```solidity
FHE.delegateUserDecryption(delegate, contractAddress, expirationTimestamp);
FHE.delegateUserDecryptionWithoutExpiration(delegate, contractAddress);
FHE.revokeUserDecryptionDelegation(delegate, contractAddress);

bool active = FHE.isDelegatedForUserDecryption(user, delegate, contractAddress, handle);
uint64 exp  = FHE.getDelegatedUserDecryptionExpirationDate(user, delegate, contractAddress);
```

Batch:
```solidity
address[] memory cs = new address[](2);
cs[0] = address(a); cs[1] = address(b);
FHE.delegateUserDecryptions(delegate, cs, expiration);
FHE.revokeUserDecryptionDelegations(delegate, cs);
```

## Encrypted Types

| Type | Bits | Operations |
|---|---|---|
| `ebool` | 2 | and, or, xor, eq, ne, not, select, rand |
| `euint8`–`euint128` | 8–128 | add, sub, mul, div*, rem*, and/or/xor, shl/shr/rotl/rotr, eq/ne/ge/gt/le/lt, min/max, neg, not, select, rand, randBounded |
| `euint160` (`eaddress`) | 160 | eq, ne, select |
| `euint256` | 256 | bit ops, shifts, eq/ne, neg, not, select, rand, randBounded |

\* `div`/`rem` only accept **plaintext** divisors.

### Creating encrypted values

```solidity
// From user input — real confidentiality
euint64 v = FHE.fromExternal(externalValue, inputProof);
FHE.allowThis(v);

// On-chain randomness (upper bound must be a power of 2)
euint8 die = FHE.randEuint8(FHE.asEuint8(8));

// Casting
euint64 big = FHE.asEuint64(small32);
euint8  tin = FHE.asEuint8(big);   // truncates
```

### Trivial encryption

`FHE.asEuintX(plaintext)` is **NOT confidential** — the plaintext is in the calldata. Only use for constants (zero init, increment-by-1, etc.).

## Constraints & Patterns

- **`ebool` is not `bool`** — cannot be used in `if`. Use `FHE.select(cond, ifTrue, ifFalse)`.
- **No decrypt in view functions** — decryption is async.
- **Wrapping arithmetic** — all FHE math is unchecked. Detect overflow with `FHE.lt(sum, original)` and `FHE.select`.
- **Gas** — FHE ops cost 20–100× a normal op. Prefer scalar operands: `FHE.add(x, 42)` is much cheaper than `FHE.add(x, FHE.asEuint32(42))`.
- **Shifts** — `shl`/`shr` shift modulo bit width.
- **Variable shadowing** — don't name a local the same as the enclosing function.

### Conditional update

```solidity
ebool isOwner = FHE.eq(addr, owner);
balance = FHE.select(isOwner, newBalance, balance);
```

### Overflow protection

```solidity
euint32 sum = FHE.add(balance, amount);
ebool overflow = FHE.lt(sum, balance);
balance = FHE.select(overflow, balance, sum);
```

## Public Decryption (production)

Async via the Gateway. Three steps:

1. Mark the handle:
   ```solidity
   FHE.makePubliclyDecryptable(value);
   ```
2. Off-chain relayer SDK calls `publicDecrypt(handles)` → KMS-signed cleartext + proof.
3. Submit on-chain:
   ```solidity
   function callbackDecryption(bytes memory cleartexts, bytes memory proof) external {
       bytes32[] memory list = new bytes32[](1);
       list[0] = FHE.toBytes32(value);
       FHE.checkSignatures(list, cleartexts, proof);  // reverts if bad
       uint64 clear = abi.decode(cleartexts, (uint64));
   }
   ```

The handle order in `list` must match the order used off-chain.

Helpers: `FHE.isPubliclyDecryptable(handle)`, `FHE.isPublicDecryptionResultValid(...)`.

## Production vs Test API

These do NOT exist in production `FHE.sol`:
- `FHE.decrypt()` — use the Gateway flow above
- `FHE.allowPublic()` — use `FHE.makePubliclyDecryptable()`

These are **test-only** (FhevmTest helpers, not callable from contracts):
`decrypt`, `userDecrypt`, `encryptUint64`, `publicDecrypt`.

For production results, expose encrypted handles via getters and decrypt them in tests.

## Common Issues

- **"User is not authorized to decrypt"** — ACL denied. Only the balance owner can decrypt their balance; for contract-level values like `confidentialTotalSupply()`, check who got `FHE.allow`.
- **Wrong decimals** — ERC-7984 uses **6 decimals**, not 18.
