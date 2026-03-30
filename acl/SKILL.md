---
name: acl
description: Access Control Lists for encrypted values in FHEVM. Who can use and decrypt encrypted data. This is where most FHEVM bugs live — forgetting ACL permissions is the #1 mistake.
---

# ACL — Access Control for Encrypted Values

## What You Probably Got Wrong

**You forgot `FHE.allowThis()`.** After storing an encrypted value, the contract itself doesn't automatically have permission to use it on the next call. You must explicitly grant the contract access. This compiles, deploys, and then silently fails at runtime.

**You think ACL is like `onlyOwner`.** ACL is not about who can call a function — it's about who can **perform FHE operations on a specific encrypted value**. A function can be public, but if the caller doesn't have ACL access to the encrypted values involved, the FHE operations will fail.

**You used `allow()` when you meant `allowTransient()`.** `allow()` stores a permanent permission onchain (costs gas for storage). `allowTransient()` grants access only for the current transaction (cheaper, no storage). Use transient when passing encrypted values between contracts in the same transaction.

---

## How ACL Works

Every encrypted value in FHEVM is identified by a handle (a `uint256`). The ACL contract maintains a mapping:

```
handle → set of authorized addresses
```

When you perform an FHE operation (`FHE.add(a, b)`), the coprocessor checks that `msg.sender` (the contract calling the operation) has ACL permission for both `a` and `b`. If not, the operation fails.

### The Lifecycle of an Encrypted Value

```
1. Value created (FHE.add, FHE.fromExternal, FHE.asEuint64, etc.)
   → ACL is EMPTY — nobody can use this value

2. FHE.allowThis(value)
   → The contract itself can now use this value in future transactions

3. FHE.allow(value, userAddress)
   → The user can now decrypt this value (read their own balance, etc.)

4. Value stored in mapping (balances[user] = value)
   → On the next call, the contract reads balances[user]
   → Contract needs ACL permission (from step 2) to use it
   → Without step 2, this FAILS
```

---

## Granting Permissions

### Permanent Permission (stored onchain)

```solidity
// Grant the CONTRACT itself permission to use a value
FHE.allowThis(encryptedValue);

// Grant a specific ADDRESS permission
FHE.allow(encryptedValue, accountAddress);
```

Use `allow()` for:
- Contract self-access (`allowThis`) — **required after every state update**
- User access to their own data (balances, votes, positions)
- Other contracts that need to read/use the value in future transactions

### Transient Permission (current transaction only)

```solidity
// Grant access for THIS TRANSACTION ONLY — no storage cost
FHE.allowTransient(encryptedValue, accountAddress);
```

Use `allowTransient()` for:
- Passing encrypted values between contracts in the same transaction
- Temporary computation helpers
- Return values that the caller needs to use immediately

### Public Decryption

```solidity
// Make value decryptable by ANYONE
FHE.makePubliclyDecryptable(encryptedValue);
```

Use for:
- Auction results after the auction closes
- Vote tallies after the voting deadline
- Any value that transitions from private to public

### Checking Permissions

```solidity
// Check if msg.sender has permission
require(FHE.isSenderAllowed(amount), "Sender not allowed");

// Check if any address has permission
bool canAccess = FHE.isAllowed(handle, account);

// Check if value is publicly decryptable
bool isPublic = FHE.isPubliclyDecryptable(handle);
```

---

## The Essential Pattern

**This pattern must appear after EVERY encrypted state update. No exceptions.**

```solidity
function updateBalance(address user, euint64 newBalance) internal {
    // 1. Store the value
    balances[user] = newBalance;

    // 2. Grant contract permission (so it can use the value next time)
    FHE.allowThis(newBalance);

    // 3. Grant user permission (so they can decrypt their balance)
    FHE.allow(newBalance, user);
}
```

### Why Both?

- **`FHE.allowThis()`** — Without this, the contract can't read `balances[user]` on the next transaction. The value is stored but inaccessible to its own contract.

- **`FHE.allow(value, user)`** — Without this, the user can't decrypt their own balance. They can see that they *have* a balance (the mapping exists), but they can't read the amount.

---

## ACL in Common Patterns

### Transfer (Two Users)

```solidity
function _transfer(address from, address to, euint64 amount) internal {
    // Update sender balance
    euint64 newFrom = FHE.sub(balances[from], amount);
    balances[from] = newFrom;
    FHE.allowThis(newFrom);      // Contract can use sender's balance
    FHE.allow(newFrom, from);    // Sender can decrypt their balance

    // Update recipient balance
    euint64 newTo = FHE.add(balances[to], amount);
    balances[to] = newTo;
    FHE.allowThis(newTo);        // Contract can use recipient's balance
    FHE.allow(newTo, to);        // Recipient can decrypt their balance
}
```

**Four ACL calls for one transfer.** Every new encrypted value needs its permissions set.

### Conditional Transfer

```solidity
function safeTransfer(address to, euint64 amount) public {
    ebool canTransfer = FHE.le(amount, balances[msg.sender]);
    euint64 transferValue = FHE.select(canTransfer, amount, FHE.asEuint64(0));

    // transferValue is a NEW encrypted value — needs ACL
    // Even though it might equal amount or zero, it's a new handle

    euint64 newFrom = FHE.sub(balances[msg.sender], transferValue);
    balances[msg.sender] = newFrom;
    FHE.allowThis(newFrom);
    FHE.allow(newFrom, msg.sender);

    euint64 newTo = FHE.add(balances[to], transferValue);
    balances[to] = newTo;
    FHE.allowThis(newTo);
    FHE.allow(newTo, to);
}
```

### Multi-Party Access

```solidity
// Grant multiple addresses access to the same value
function grantAccess(euint64 value, address[] memory authorized) internal {
    FHE.allowThis(value);
    for (uint i = 0; i < authorized.length; i++) {
        FHE.allow(value, authorized[i]);
    }
}
```

---

## Decryption Patterns

### User Decryption

Users with ACL permission can decrypt values client-side. The contract doesn't need to do anything special — just grant `FHE.allow(value, user)`.

### Public Decryption (On-chain Reveal)

```solidity
// Step 1: Make value publicly decryptable
FHE.makePubliclyDecryptable(encryptedResult);

// Step 2: Anyone can verify decryption with KMS signatures
function verifyDecryption(
    bytes32[] memory handles,
    bytes memory clearResult,
    bytes memory decryptionProof
) public {
    FHE.checkSignatures(handles, clearResult, decryptionProof);
    // Use the clear result
    bool result = abi.decode(clearResult, (bool));
}
```

### Delegation

```solidity
// Allow another address to decrypt on your behalf
FHE.delegateForUserDecryption(
    delegate,         // Who can decrypt
    contractAddress,  // For which contract's values
    expirationDate    // Unix timestamp
);

// Revoke delegation
FHE.revokeDelegationForUserDecryption(delegate, contractAddress);

// Check delegation
uint64 expiry = FHE.getUserDecryptionDelegationExpirationDate(
    delegator, delegate, contractAddress
);
```

---

## Common Mistakes

### 1. Missing `allowThis()` — The #1 Bug

```solidity
// ❌ WRONG — contract can't use this value on the next call
balances[user] = FHE.add(balances[user], amount);

// ✅ CORRECT
balances[user] = FHE.add(balances[user], amount);
FHE.allowThis(balances[user]);
FHE.allow(balances[user], user);
```

### 2. Forgetting ACL for Intermediate Values

```solidity
// ❌ WRONG — if you store `result`, it needs ACL
euint64 result = FHE.mul(a, b);
storedResults[id] = result;
// Missing: FHE.allowThis(result);

// ✅ CORRECT
euint64 result = FHE.mul(a, b);
storedResults[id] = result;
FHE.allowThis(result);
```

### 3. Using `allow()` When `allowTransient()` Would Suffice

```solidity
// ❌ WASTEFUL — permanent ACL storage for a value only needed this tx
FHE.allow(tempValue, helperContract);

// ✅ BETTER — transient permission, no storage cost
FHE.allowTransient(tempValue, helperContract);
```

### 4. Not Granting User Access

```solidity
// ❌ WRONG — user can't decrypt their own balance
balances[user] = newBalance;
FHE.allowThis(newBalance);
// Missing: FHE.allow(newBalance, user);

// ✅ CORRECT — user can see their balance
balances[user] = newBalance;
FHE.allowThis(newBalance);
FHE.allow(newBalance, user);
```

---

## Checklist

Before deploying any FHEVM contract:

- [ ] Every encrypted state update has `FHE.allowThis()` immediately after
- [ ] Every user-facing encrypted value has `FHE.allow(value, user)`
- [ ] Temporary cross-contract values use `allowTransient()` not `allow()`
- [ ] Input validation uses `FHE.isSenderAllowed()` where appropriate
- [ ] Public reveals use `FHE.makePubliclyDecryptable()` at the right time
- [ ] No encrypted value is stored without at least `FHE.allowThis()`
