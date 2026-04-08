---
name: solidity
description: Complete guide to writing encrypted smart contracts with FHEVM. Covers encrypted types, FHE operations, ACL, patterns, gas optimization, security, testing, deployment, and migration. The single reference for all Solidity + FHEVM development.
---

# Solidity — Encrypted Smart Contracts with FHEVM

## What You Probably Got Wrong

**You used `euint256` for everything.** `euint64` is the standard for balances. Larger types cost dramatically more HCU for every operation.

**You forgot `FHE.allowThis()`.** After storing an encrypted value, the contract itself doesn't have permission to use it on the next call. This compiles, deploys, and silently fails at runtime. The #1 FHEVM bug.

**You tried `if (FHE.gt(a, b))`.** You cannot branch on encrypted values. `FHE.gt()` returns an `ebool` — an encrypted boolean. Use `FHE.select()`.

**You tried `FHE.div(a, encryptedB)`.** Division and remainder only work with plaintext divisors. Fundamental limitation of the current FHE scheme.

**You marked FHE functions as `view`.** FHE operations interact with the coprocessor — they're state-changing. Remove `view` from any function with FHE operations.

**You confused `FHE.asEuint64(100)` with real encryption.** Trivial encryption wraps a plaintext — everyone can see it onchain. Only `FHE.fromExternal()` is truly private.

**You emitted transfer amounts in events.** Confidential ERC-20 events emit `from` and `to` but NOT the amount.

**You think regular Solidity security is enough.** FHEVM adds a new class of bugs: ACL misconfig, information leaks through control flow, trivial encryption confusion.

**You skipped ACL testing.** The most common FHEVM bug is missing ACL permissions. If you don't test that unauthorized addresses get rejected, you'll ship broken access control.

**You only tested the happy path.** FHE contracts silently handle failures via `FHE.select`. If a transfer fails, it transfers 0 — it doesn't revert. Test the zero-transfer case.

**You deployed to mainnet without testing on Sepolia.** FHE operations consume real coprocessor resources. Test on Sepolia first — always.

**You think FHE operations cost regular gas.** They don't. FHE operations are metered using **Homomorphic Complexity Units (HCU)**. Per-transaction limit is **20,000,000 HCU**. A single `FHE.mul(euint64, euint64)` costs **596,000 HCU**.

---

## Contract Setup

```solidity
// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.24;

import "@fhevm/solidity/lib/FHE.sol";
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaConfig.sol";

contract MyContract is ZamaEthereumConfig {
    // ZamaEthereumConfig auto-configures the coprocessor
    // for Ethereum mainnet (chainId=1) or Sepolia (chainId=11155111)

    euint64 private secretValue;
}
```

Manual configuration (if not using ZamaEthereumConfig):

```solidity
import "@fhevm/solidity/lib/FHE.sol";
import {CoprocessorSetup} from "./CoprocessorSetup.sol";

contract MyContract {
    constructor() {
        FHE.setCoprocessor(CoprocessorSetup.defaultConfig());
    }
}
```

---

## Encrypted Types

### Storage Types

| Type | Description | Use Case |
|------|-------------|----------|
| `ebool` | Encrypted boolean | Flags, conditions |
| `euint8` | Encrypted 8-bit uint | Small counters, categories |
| `euint16` | Encrypted 16-bit uint | Medium counters |
| `euint32` | Encrypted 32-bit uint | Timestamps, IDs |
| `euint64` | Encrypted 64-bit uint | **Default for balances** |
| `euint128` | Encrypted 128-bit uint | Large values |
| `euint256` | Encrypted 256-bit uint | Full precision (expensive, limited ops) |
| `eaddress` | Encrypted address | Private recipients |

**Use `euint64` by default.** Larger types cost more gas for every operation.

### External Input Types

Users submit encrypted values as handles. These types represent unvalidated input:

| Type | Maps to |
|------|---------|
| `externalEbool` | `ebool` after validation |
| `externalEuint8` | `euint8` after validation |
| `externalEuint16` | `euint16` after validation |
| `externalEuint32` | `euint32` after validation |
| `externalEuint64` | `euint64` after validation |
| `externalEuint128` | `euint128` after validation |
| `externalEuint256` | `euint256` after validation |
| `externalEaddress` | `eaddress` after validation |

Always convert external inputs with `FHE.fromExternal(handle, inputProof)` before use.

---

## FHE Operations

### Arithmetic

```solidity
euint64 sum = FHE.add(a, b);        // a + b
euint64 diff = FHE.sub(a, b);       // a - b
euint64 prod = FHE.mul(a, b);       // a * b
euint64 quot = FHE.div(a, 10);      // a / 10 (PLAINTEXT divisor ONLY)
euint64 rem = FHE.rem(a, 10);       // a % 10 (PLAINTEXT divisor ONLY)
euint64 minimum = FHE.min(a, b);    // min(a, b)
euint64 maximum = FHE.max(a, b);    // max(a, b)
euint64 negated = FHE.neg(a);       // -a (modular negation)
```

**Critical:** `FHE.div()` and `FHE.rem()` only accept plaintext (non-encrypted) divisors. `FHE.div(a, encryptedB)` does not exist.

### Comparison (return `ebool`)

```solidity
ebool isEqual = FHE.eq(a, b);       // a == b
ebool notEqual = FHE.ne(a, b);      // a != b
ebool lessThan = FHE.lt(a, b);      // a < b
ebool lessOrEq = FHE.le(a, b);      // a <= b
ebool greaterThan = FHE.gt(a, b);   // a > b
ebool greaterOrEq = FHE.ge(a, b);   // a >= b
```

**These return `ebool` — an encrypted boolean. You CANNOT use the result in `if`, `require`, or `while`.** Use `FHE.select()` to branch.

### Bitwise

```solidity
euint64 andResult = FHE.and(a, b);   // a & b
euint64 orResult = FHE.or(a, b);     // a | b
euint64 xorResult = FHE.xor(a, b);   // a ^ b
euint64 notResult = FHE.not(a);      // ~a
euint64 shifted = FHE.shl(a, 2);    // a << 2
euint64 rShifted = FHE.shr(a, 2);   // a >> 2
euint64 rotLeft = FHE.rotl(a, 2);   // rotate left
euint64 rotRight = FHE.rotr(a, 2);  // rotate right
```

### Conditional Selection (THE CORE PATTERN)

```solidity
// FHE.select is the ONLY way to branch on encrypted conditions
euint64 result = FHE.select(
    condition,     // ebool — encrypted boolean
    valueIfTrue,   // euint64
    valueIfFalse   // euint64
);

// Example: conditional transfer (transfer amount or zero)
euint64 transferValue = FHE.select(canTransfer, amount, FHE.asEuint64(0));
```

`FHE.select()` always evaluates both branches. That's what makes it private — observers can't tell which value was selected.

### Random Number Generation

```solidity
ebool randomBool = FHE.randEbool();
euint8 random8 = FHE.randEuint8();
euint16 random16 = FHE.randEuint16();
euint32 random32 = FHE.randEuint32();
euint64 random64 = FHE.randEuint64();

// Bounded random — upperBound MUST be a power of 2
euint8 bounded = FHE.randEuint8(16);     // 0 to 15  (2^4)
euint64 bounded64 = FHE.randEuint64(1024); // 0 to 1023 (2^10)
```

**Critical:** `FHE.randEuint8(100)` is WRONG. The upper bound must be a power of 2. Use `FHE.randEuint8(128)`.

### Type Casting

```solidity
// Upcast (safe — no data loss)
euint16 bigger = FHE.asEuint16(euint8Value);
euint64 bigger64 = FHE.asEuint64(euint32Value);

// Downcast (TRUNCATES — data loss possible)
euint8 smaller = FHE.asEuint8(euint64Value);

// Trivial encrypt (plaintext → ciphertext — NOT private!)
euint64 encrypted = FHE.asEuint64(100);  // Value 100 is visible onchain
ebool encBool = FHE.asEbool(true);

// Bool conversion
ebool fromInt = FHE.asEbool(euint8Value);   // Non-zero = true
euint8 fromBool = FHE.asEuint8(eboolValue); // true = 1, false = 0
```

### Initialization Check

```solidity
if (!FHE.isInitialized(value)) {
    value = FHE.asEuint64(0); // Default to encrypted zero
}
```

Always check `FHE.isInitialized()` before operating on values that might not have been set.

---

## Handling Encrypted Inputs

### Function Signature Pattern

```solidity
function transfer(
    address to,
    externalEuint64 encryptedAmount,  // Handle from client
    bytes calldata inputProof         // ZK proof of valid encryption
) public returns (bool) {
    // Validate and convert — ALWAYS do this first
    euint64 amount = FHE.fromExternal(encryptedAmount, inputProof);
    // Now use 'amount' for FHE operations
}
```

### Multiple Encrypted Inputs

```solidity
function multiInput(
    externalEbool flag,
    externalEuint64 amount,
    externalEuint8 category,
    bytes calldata inputProof   // Single proof covers ALL inputs
) public {
    ebool validFlag = FHE.fromExternal(flag, inputProof);
    euint64 validAmount = FHE.fromExternal(amount, inputProof);
    euint8 validCategory = FHE.fromExternal(category, inputProof);
}
```

### Comparing Encrypted with Plaintext

```solidity
ebool isPositive = FHE.gt(encryptedValue, 0);
ebool isMax = FHE.eq(encryptedValue, type(uint64).max);
euint64 capped = FHE.min(encryptedValue, 1000);
```

---

## Access Control (ACL)

### How ACL Works

Every encrypted value is identified by a handle. The ACL contract maintains: `handle → set of authorized addresses`.

When you perform an FHE operation, the coprocessor checks that `msg.sender` (the calling contract) has ACL permission for all operands. If not, the operation fails.

```
1. Value created (FHE.add, FHE.fromExternal, FHE.asEuint64, etc.)
   → ACL is EMPTY — nobody can use this value

2. FHE.allowThis(value)
   → The contract itself can now use this value in future transactions

3. FHE.allow(value, userAddress)
   → The user can now decrypt this value

4. Value stored in mapping (balances[user] = value)
   → On the next call, the contract reads balances[user]
   → Contract needs ACL permission (from step 2) to use it
   → Without step 2, this FAILS SILENTLY
```

### Granting Permissions

```solidity
// PERMANENT permission — stored onchain
FHE.allowThis(encryptedValue);           // Contract can use it
FHE.allow(encryptedValue, accountAddress); // Address can use/decrypt it

// TRANSIENT permission — current transaction only, no storage cost
FHE.allowTransient(encryptedValue, accountAddress);

// PUBLIC decryption — anyone can decrypt
FHE.makePubliclyDecryptable(encryptedValue);
```

### Checking Permissions

```solidity
require(FHE.isSenderAllowed(amount), "Sender not allowed");
bool canAccess = FHE.isAllowed(handle, account);
bool isPublic = FHE.isPubliclyDecryptable(handle);
```

### The Essential Pattern

**This must appear after EVERY encrypted state update. No exceptions.**

```solidity
function updateBalance(address user, euint64 newBalance) internal {
    balances[user] = newBalance;
    FHE.allowThis(newBalance);        // Contract can use it next time
    FHE.allow(newBalance, user);      // User can decrypt their balance
}
```

### ACL in Transfers

```solidity
function _transfer(address from, address to, euint64 amount) internal {
    euint64 newFrom = FHE.sub(balances[from], amount);
    balances[from] = newFrom;
    FHE.allowThis(newFrom);
    FHE.allow(newFrom, from);

    euint64 newTo = FHE.add(balances[to], amount);
    balances[to] = newTo;
    FHE.allowThis(newTo);
    FHE.allow(newTo, to);
}
```

**Four ACL calls for one transfer.** Every new encrypted value needs its permissions set.

### Decryption Patterns

#### User Decryption
Users with ACL permission decrypt client-side. Just grant `FHE.allow(value, user)`.

#### Public Decryption (On-chain Reveal)

```solidity
FHE.makePubliclyDecryptable(encryptedResult);

function verifyDecryption(
    bytes32[] memory handles,
    bytes memory clearResult,
    bytes memory decryptionProof
) public {
    FHE.checkSignatures(handles, clearResult, decryptionProof);
    bool result = abi.decode(clearResult, (bool));
}
```

#### Delegation

```solidity
FHE.delegateForUserDecryption(delegate, contractAddress, expirationDate);
FHE.revokeDelegationForUserDecryption(delegate, contractAddress);
uint64 expiry = FHE.getUserDecryptionDelegationExpirationDate(
    delegator, delegate, contractAddress
);
```

### Common ACL Mistakes

```solidity
// ❌ WRONG — contract can't use this value on the next call
balances[user] = FHE.add(balances[user], amount);

// ✅ CORRECT
balances[user] = FHE.add(balances[user], amount);
FHE.allowThis(balances[user]);
FHE.allow(balances[user], user);
```

```solidity
// ❌ WASTEFUL — permanent ACL for a temp value
FHE.allow(tempValue, helperContract);

// ✅ BETTER — transient permission
FHE.allowTransient(tempValue, helperContract);
```

---

## FHE Gas (Homomorphic Complexity Units)

### HCU Limits

| Limit | Value | What Happens |
|-------|-------|-------------|
| Global HCU per transaction | **20,000,000** | Transaction reverts |
| Sequential depth HCU per transaction | **5,000,000** | Transaction reverts |

### Quick Reference: euint64 Operations

| Operation | Scalar HCU | Non-scalar HCU | Budget at 20M |
|-----------|-----------|----------------|---------------|
| `FHE.add` | 133,000 | 162,000 | ~123 ops |
| `FHE.sub` | 133,000 | 162,000 | ~123 ops |
| `FHE.mul` | 365,000 | 596,000 | ~33 ops |
| `FHE.div` (plaintext only) | 715,000 | — | ~27 ops |
| `FHE.rem` (plaintext only) | 1,153,000 | — | ~17 ops |
| `FHE.eq` | 83,000 | 120,000 | ~166 ops |
| `FHE.gt` / `FHE.lt` | ~118,000 | ~152,000 | ~131 ops |
| `FHE.select` | — | 55,000 | ~363 ops |
| `FHE.min` / `FHE.max` | ~150,000 | ~219,000 | ~91 ops |
| `FHE.randEuint64` | — | 24,000 | ~833 ops |
| `FHE.not` | — | 63 | ~317K ops |
| `cast` | — | 32 | negligible |
| `trivialEncrypt` | — | 32 | negligible |

**Scalar** = one operand is plaintext (e.g., `FHE.add(encrypted, 5)`). Always cheaper.

### Full HCU Cost Tables

#### ebool

| Operation | Scalar | Non-scalar |
|-----------|--------|-----------|
| `and` | 22,000 | 25,000 |
| `or` | 22,000 | 24,000 |
| `xor` | 2,000 | 22,000 |
| `not` | — | 2 |
| `select` | — | 55,000 |
| `randEbool` | — | 19,000 |

#### euint8

| Operation | Scalar | Non-scalar |
|-----------|--------|-----------|
| `add` | 84,000 | 88,000 |
| `sub` | 84,000 | 91,000 |
| `mul` | 122,000 | 150,000 |
| `div` | 210,000 | — |
| `rem` | 440,000 | — |
| `eq` / `ne` | 55,000 | 55,000 |
| `ge` / `gt` / `le` / `lt` | ~52-58K | ~58-63K |
| `min` / `max` | ~84-89K | ~119-121K |
| `shr` / `shl` | 32,000 | ~91-92K |
| `and` / `or` / `xor` | ~30-31K | ~30-31K |
| `neg` | — | 79,000 |
| `not` | — | 9 |
| `select` | — | 55,000 |
| `randEuint8` | — | 23,000 |

#### euint16

| Operation | Scalar | Non-scalar |
|-----------|--------|-----------|
| `add` / `sub` | 93,000 | 93,000 |
| `mul` | 193,000 | 222,000 |
| `div` | 302,000 | — |
| `rem` | 580,000 | — |
| `eq` / `ne` | 55,000 | 83,000 |
| `ge` / `gt` / `le` / `lt` | ~55-58K | ~83-84K |
| `min` / `max` | ~88-89K | ~145-146K |
| `select` | — | 55,000 |
| `randEuint16` | — | 23,000 |

#### euint32

| Operation | Scalar | Non-scalar |
|-----------|--------|-----------|
| `add` / `sub` | 95,000 | 125,000 |
| `mul` | 265,000 | 328,000 |
| `div` | 438,000 | — |
| `rem` | 792,000 | — |
| `eq` / `ne` | ~82-83K | ~85-86K |
| `ge` / `gt` / `le` / `lt` | ~83-84K | ~117-118K |
| `min` / `max` | 117,000 | ~180-182K |
| `select` | — | 55,000 |
| `randEuint32` | — | 24,000 |

#### euint64

| Operation | Scalar | Non-scalar |
|-----------|--------|-----------|
| `add` / `sub` | 133,000 | 162,000 |
| `mul` | 365,000 | 596,000 |
| `div` | 715,000 | — |
| `rem` | 1,153,000 | — |
| `eq` / `ne` | ~83-84K | ~118-120K |
| `ge` / `gt` / `le` / `lt` | ~116-119K | ~146-152K |
| `min` / `max` | ~149-150K | ~218-219K |
| `neg` | — | 131,000 |
| `not` | — | 63 |
| `select` | — | 55,000 |
| `randEuint64` | — | 24,000 |

#### euint128

| Operation | Scalar | Non-scalar |
|-----------|--------|-----------|
| `add` / `sub` | 172,000 | ~259-260K |
| `mul` | 696,000 | 1,686,000 |
| `div` | 1,225,000 | — |
| `rem` | 1,943,000 | — |
| `eq` / `ne` | 117,000 | 122,000 |
| `ge` / `gt` / `le` / `lt` | ~149-150K | ~210-218K |
| `min` / `max` | ~180-186K | ~289-290K |
| `neg` | — | 168,000 |
| `not` | — | 130 |
| `select` | — | 57,000 |
| `randEuint128` | — | 25,000 |

#### euint256 (Limited Operations)

Only bitwise, shift, comparison, and select. **No `add`, `sub`, `mul`, `div`.**

| Operation | Scalar | Non-scalar |
|-----------|--------|-----------|
| `and` / `or` / `xor` | ~38-39K | ~38-39K |
| `shr` / `shl` | ~38-39K | ~369-378K |
| `eq` / `ne` | ~117-118K | ~150-152K |
| `neg` | — | 269,000 |
| `not` | — | 130 |
| `select` | — | 108,000 |
| `randEuint256` | — | 30,000 |

#### eaddress

| Operation | Scalar | Non-scalar |
|-----------|--------|-----------|
| `eq` | 115,000 | 125,000 |
| `ne` | 115,000 | 124,000 |
| `select` | — | 83,000 |

#### Misc

| Operation | HCU |
|-----------|-----|
| `cast` | 32 |
| `trivialEncrypt` | 32 |
| `randBounded` | 23,000–30,000 |

### Optimization Patterns

#### Use Scalar Operations

```solidity
// ✅ Cheaper — plaintext divisor
euint64 result = FHE.div(amount, 2);  // 715,000 HCU (scalar)
```

#### Use the Smallest Type

| Value range | Type | add HCU |
|-------------|------|---------|
| 0–255 | euint8 | 88,000 |
| 0–65,535 | euint16 | 93,000 |
| 0–4.2B | euint32 | 125,000 |
| 0–18.4Q | euint64 | 162,000 |
| Larger | euint128 | 259,000 |

#### Avoid Loops Over Encrypted Values

```solidity
// ❌ 10 × (add + gt + select) = 3,690,000 HCU — near depth limit
for (uint i = 0; i < 10; i++) {
    result = FHE.add(result, values[i]);
    ebool check = FHE.gt(result, threshold);
    result = FHE.select(check, result, threshold);
}

// ✅ Batch add first, one comparison: 1,839K HCU
for (uint i = 0; i < 10; i++) {
    result = FHE.add(result, values[i]);
}
result = FHE.min(result, threshold);
```

### Estimating HCU: Transfer Example

```
FHE.fromExternal:  ~0 HCU
FHE.le (compare):  149,000 HCU
FHE.select:        55,000 HCU
FHE.asEuint64:     32 HCU
FHE.sub (sender):  162,000 HCU
FHE.add (recipient): 162,000 HCU
Total: ~528,000 HCU (2.6% of limit) ✅
```

---

## Patterns

### 1. Confidential ERC-20

```solidity
// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.24;

import "@fhevm/solidity/lib/FHE.sol";
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaConfig.sol";
import "@openzeppelin/contracts/access/Ownable2Step.sol";

contract ConfidentialERC20 is Ownable2Step, ZamaEthereumConfig {
    mapping(address => euint64) internal balances;
    mapping(address => mapping(address => euint64)) internal allowances;

    uint64 private _totalSupply;  // Public — total supply is not secret
    string private _name;
    string private _symbol;
    uint8 public constant decimals = 6;

    // Events: addresses are public, amounts are NOT
    event Transfer(address indexed from, address indexed to);
    event Approval(address indexed owner, address indexed spender);

    constructor(string memory name_, string memory symbol_) Ownable(msg.sender) {
        _name = name_;
        _symbol = symbol_;
    }

    function mint(uint64 amount) public onlyOwner {
        balances[owner()] = FHE.add(balances[owner()], amount);
        FHE.allowThis(balances[owner()]);
        FHE.allow(balances[owner()], owner());
        _totalSupply += amount;
    }

    function transfer(
        address to,
        externalEuint64 encryptedAmount,
        bytes calldata inputProof
    ) public returns (bool) {
        euint64 amount = FHE.fromExternal(encryptedAmount, inputProof);
        require(FHE.isSenderAllowed(amount), "Not allowed");

        ebool canTransfer = FHE.le(amount, balances[msg.sender]);
        _transfer(msg.sender, to, amount, canTransfer);
        return true;
    }

    function _transfer(
        address from, address to, euint64 amount, ebool canTransfer
    ) internal {
        euint64 transferValue = FHE.select(canTransfer, amount, FHE.asEuint64(0));

        euint64 newBalanceTo = FHE.add(balances[to], transferValue);
        balances[to] = newBalanceTo;
        FHE.allowThis(newBalanceTo);
        FHE.allow(newBalanceTo, to);

        euint64 newBalanceFrom = FHE.sub(balances[from], transferValue);
        balances[from] = newBalanceFrom;
        FHE.allowThis(newBalanceFrom);
        FHE.allow(newBalanceFrom, from);

        emit Transfer(from, to);
    }

    function balanceOf(address wallet) public view returns (euint64) {
        return balances[wallet];
    }
}
```

**Key design decisions:**
- `_totalSupply` is plaintext — hiding market cap is usually not needed
- `decimals` is `6` (like USDC) — `euint64` max is ~18.4 quintillion
- `Transfer` event has no amount — intentional
- Failed transfers are silent no-ops (transfer 0) — preserves privacy

### 2. Encrypted Voting

```solidity
contract ConfidentialVoting is ZamaEthereumConfig {
    euint64 public encryptedYesCount;
    euint64 public encryptedNoCount;
    mapping(address => bool) public hasVoted;
    uint256 public deadline;
    bool public revealed;

    constructor(uint256 _duration) {
        deadline = block.timestamp + _duration;
        encryptedYesCount = FHE.asEuint64(0);
        encryptedNoCount = FHE.asEuint64(0);
        FHE.allowThis(encryptedYesCount);
        FHE.allowThis(encryptedNoCount);
    }

    function vote(externalEbool encryptedVote, bytes calldata inputProof) public {
        require(block.timestamp < deadline, "Voting ended");
        require(!hasVoted[msg.sender], "Already voted");
        hasVoted[msg.sender] = true;

        ebool isYes = FHE.fromExternal(encryptedVote, inputProof);
        euint64 one = FHE.asEuint64(1);
        euint64 zero = FHE.asEuint64(0);

        encryptedYesCount = FHE.add(encryptedYesCount, FHE.select(isYes, one, zero));
        encryptedNoCount = FHE.add(encryptedNoCount, FHE.select(isYes, zero, one));

        FHE.allowThis(encryptedYesCount);
        FHE.allowThis(encryptedNoCount);
    }

    function reveal() public {
        require(block.timestamp >= deadline, "Voting not ended");
        require(!revealed, "Already revealed");
        revealed = true;
        FHE.makePubliclyDecryptable(encryptedYesCount);
        FHE.makePubliclyDecryptable(encryptedNoCount);
    }
}
```

### 3. Sealed-Bid Auction

```solidity
contract SealedBidAuction is ZamaEthereumConfig {
    euint64 public highestBid;
    mapping(address => euint64) public bids;
    mapping(address => uint256) public deposits;
    uint256 public deadline;
    bool public settled;

    constructor(uint256 _duration) {
        deadline = block.timestamp + _duration;
        highestBid = FHE.asEuint64(0);
        FHE.allowThis(highestBid);
    }

    function bid(externalEuint64 encryptedBid, bytes calldata inputProof) public payable {
        require(block.timestamp < deadline, "Auction ended");
        require(!FHE.isInitialized(bids[msg.sender]), "Already bid");

        euint64 bidAmount = FHE.fromExternal(encryptedBid, inputProof);
        bids[msg.sender] = bidAmount;
        deposits[msg.sender] = msg.value;

        FHE.allowThis(bidAmount);
        FHE.allow(bidAmount, msg.sender);

        ebool isHigher = FHE.gt(bidAmount, highestBid);
        highestBid = FHE.select(isHigher, bidAmount, highestBid);
        FHE.allowThis(highestBid);
    }

    function settle() public {
        require(block.timestamp >= deadline && !settled);
        settled = true;
        FHE.makePubliclyDecryptable(highestBid);
    }
}
```

### 4. Encrypted Counter

```solidity
contract ConfidentialCounter is ZamaEthereumConfig {
    euint64 private counter;

    constructor() {
        counter = FHE.asEuint64(0);
        FHE.allowThis(counter);
    }

    function increment(externalEuint64 encryptedAmount, bytes calldata inputProof) public {
        euint64 amount = FHE.fromExternal(encryptedAmount, inputProof);
        counter = FHE.add(counter, amount);
        FHE.allowThis(counter);
    }

    function revealCounter() public {
        FHE.makePubliclyDecryptable(counter);
    }
}
```

---

## Building Blocks

### ERC-7984: Confidential Token Standard

Wraps existing ERC-20 tokens into encrypted versions with private balances.

```solidity
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaConfig.sol";
import {ERC7984} from "@openzeppelin/confidential-contracts/token/ERC7984/ERC7984.sol";
import {Ownable2Step, Ownable} from "@openzeppelin/contracts/access/Ownable2Step.sol";
import {FHE, externalEuint64, euint64} from "@fhevm/solidity/lib/FHE.sol";

contract MyConfidentialToken is ZamaEthereumConfig, ERC7984, Ownable2Step {
    constructor(
        address owner, uint64 amount,
        string memory name_, string memory symbol_, string memory tokenURI_
    ) ERC7984(name_, symbol_, tokenURI_) Ownable(owner) {
        _mint(owner, FHE.asEuint64(amount));
    }
}
```

### Wrapping ERC-20 → ERC-7984

```solidity
import {ERC7984ERC20Wrapper} from "@openzeppelin/confidential-contracts/token/ERC7984/extensions/ERC7984ERC20Wrapper.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract ConfidentialUSDC is ERC7984ERC20Wrapper {
    constructor(IERC20 usdc)
        ERC7984ERC20Wrapper(usdc)
        ERC7984("Confidential USDC", "cUSDC", "") {}

    function wrap(address to, uint256 amount) public virtual {
        SafeERC20.safeTransferFrom(underlying(), msg.sender, address(this), amount);
        _mint(to, FHE.asEuint64(uint64(amount)));
    }
}
```

### Official Confidential Wrappers (Already Deployed)

**Don't build these yourself.** See `addresses/SKILL.md` for the full list:
- cUSDC, cUSDT, cWETH, cBRON, cZAMA, ctGBP, cXAUt on Ethereum mainnet
- Mock wrappers on Sepolia testnet

### OpenZeppelin Confidential Contracts

```bash
npm install @openzeppelin/confidential-contracts
```

Repository: https://github.com/OpenZeppelin/openzeppelin-confidential-contracts

Available: ERC-7984, Confidential ERC-20, Confidential voting, Confidential auctions.

### The Wrap/Unwrap Boundary

```
Public ERC-20 ──[wrap]──→ Confidential ERC-7984 (encrypted)
Confidential ERC-7984 ──[unwrap]──→ Public ERC-20 (requires async decryption)
```

Wrapping is simple. Unwrapping requires async decryption through the coprocessor — it spans multiple transactions.

You **cannot** directly compose encrypted contracts with plaintext DeFi (Uniswap, Aave). Unwrap → interact → wrap back.

---

## Security

### FHE-Specific Vulnerabilities

#### 1. ACL Misconfiguration (Critical — #1 Bug)

```solidity
// ❌ VULNERABLE — contract can't use this value on the next call
balances[user] = FHE.add(balances[user], amount);

// ✅ SAFE
balances[user] = FHE.add(balances[user], amount);
FHE.allowThis(balances[user]);
FHE.allow(balances[user], user);
```

#### 2. Information Leaks via Control Flow

```solidity
// ❌ LEAKS — revert reveals balance < amount
require(FHE.decrypt(sufficient), "Insufficient balance");

// ✅ SAFE — silent no-op
euint64 transferValue = FHE.select(canTransfer, amount, FHE.asEuint64(0));
```

Other leak vectors: gas consumption differences, conditional event emission, different return values.

#### 3. Trivial Encryption Confusion

```solidity
// ❌ NOT PRIVATE — everyone sees 1000 in bytecode
balances[msg.sender] = FHE.asEuint64(1000);

// ✅ After this, all operations produce truly encrypted results
balances[owner()] = FHE.add(balances[owner()], amount); // amount is public, intentional
```

#### 4. Uninitialized Encrypted Values

```solidity
// ❌ DANGEROUS
euint64 newBalance = FHE.sub(balances[msg.sender], amount); // might be uninitialized

// ✅ SAFE
require(FHE.isInitialized(balances[msg.sender]), "No balance");
```

#### 5. Timing Attacks on Decryption

Make decryption the LAST step, take no conditional actions after.

#### 6. Missing Input Validation

```solidity
// ❌ Bypasses input verification
euint64 val = euint64.wrap(externalEuint64.unwrap(amount));

// ✅ Always validate
euint64 val = FHE.fromExternal(amount, inputProof);
```

#### 7. Encrypted Value in Events

```solidity
// ❌ Handle changes reveal when values change
event BalanceUpdated(address user, euint64 newBalance);

// ✅ Emit only metadata
event Transfer(address indexed from, address indexed to);
```

### Standard Solidity Vulnerabilities

These still apply — encryption doesn't protect you:

- **Reentrancy:** Use CEI + `nonReentrant`. Update encrypted state BEFORE external calls.
- **Token decimals:** USDC=6, WBTC=8, DAI/WETH=18. Never hardcode `1e18`.
- **SafeERC20:** Use for all token operations (USDT doesn't return bool).
- **Access control:** `onlyOwner` or `AccessControl` on privileged functions.
- **Input validation:** Zero address, zero amount, bounds checks.
- **No floating point:** Multiply before dividing. Use basis points.
- **MEV:** Encrypted values help (amounts hidden in mempool), but function selectors are visible.
- **Oracle safety:** Chainlink with staleness check, not DEX spot price.

---

## Testing

### Setup

```typescript
import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import "@fhevm/hardhat-plugin";

const config: HardhatUserConfig = {
  solidity: "0.8.24",
};
```

```typescript
import { ethers } from "hardhat";
import { fhevm } from "hardhat";

describe("ConfidentialERC20", function () {
  let contract: ConfidentialERC20;
  let alice: SignerWithAddress;

  beforeEach(async function () {
    [alice] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("ConfidentialERC20");
    contract = await Factory.deploy("Confidential Token", "CONF");
  });
});
```

### Creating Encrypted Inputs

```typescript
const input = fhevm.createEncryptedInput(await contract.getAddress(), alice.address);
input.add64(100n);
const encrypted = await input.encrypt();

await contract.transfer(bob.address, encrypted.handles[0], encrypted.inputProof);
```

### Decrypting Values in Tests

```typescript
const encryptedBalance = await contract.balanceOf(alice.address);
const balance = await fhevm.decrypt64(encryptedBalance);
expect(balance).to.equal(1000n);
```

Type-specific: `decryptBool`, `decrypt8`, `decrypt16`, `decrypt32`, `decrypt64`, `decryptAddress`.

### What to Test

**1. Basic operations:**
```typescript
it("should transfer encrypted amount", async function () {
  await contract.mint(1000n);
  const input = fhevm.createEncryptedInput(await contract.getAddress(), alice.address);
  input.add64(300n);
  const encrypted = await input.encrypt();
  await contract.transfer(bob.address, encrypted.handles[0], encrypted.inputProof);

  expect(await fhevm.decrypt64(await contract.balanceOf(alice.address))).to.equal(700n);
  expect(await fhevm.decrypt64(await contract.balanceOf(bob.address))).to.equal(300n);
});
```

**2. Insufficient balance (silent failure):**
```typescript
it("should transfer 0 when balance is insufficient", async function () {
  await contract.mint(100n);
  const input = fhevm.createEncryptedInput(await contract.getAddress(), alice.address);
  input.add64(200n); // More than balance
  const encrypted = await input.encrypt();

  await contract.transfer(bob.address, encrypted.handles[0], encrypted.inputProof);
  // Does NOT revert — transfers 0
  expect(await fhevm.decrypt64(await contract.balanceOf(alice.address))).to.equal(100n);
  expect(await fhevm.decrypt64(await contract.balanceOf(bob.address))).to.equal(0n);
});
```

**3. ACL verification** — test that recipients get access after transfer.

**4. Edge cases** — zero transfer, max values, uninitialized balances, self-transfer.

**5. Access control** — unauthorized callers revert on privileged functions.

**6. Property tests** — invariants hold across sequences (e.g., sum of balances = total minted).

### What NOT to Test

- FHE math correctness (Zama's responsibility)
- ACL contract internals
- OpenZeppelin internals
- Getters that return constructor params

---

## Migration — Adding FHE to Existing Contracts

### Step 1: Identify What to Encrypt

Only encrypt what needs privacy. Keep public values plaintext.

- **Encrypt:** balances, transfer amounts, votes, bids, personal data
- **Keep plaintext:** names, symbols, decimals, total supply, timestamps, addresses

### Step 2: Change Types

`uint256` → `euint64`, `bool` → `ebool` for private values. Add `ZamaEthereumConfig`.

### Step 3: Update Function Signatures

Add `externalEuint64` + `bytes calldata inputProof` parameters.

### Step 4: Rewrite Branching Logic

Every `if/require` on encrypted values → `FHE.select()`.

```solidity
// BEFORE
require(balances[msg.sender] >= amount, "Insufficient balance");
balances[msg.sender] -= amount;

// AFTER
ebool canTransfer = FHE.le(amount, balances[msg.sender]);
euint64 transferValue = FHE.select(canTransfer, amount, FHE.asEuint64(0));
euint64 newFrom = FHE.sub(balances[msg.sender], transferValue);
```

### Step 5: Add ACL

`FHE.allowThis()` + `FHE.allow()` after every encrypted state update.

### Step 6: Update Events

Remove encrypted values from events. Emit addresses only.

### Step 7: Update Return Types

`balanceOf` returns `euint64`, not `uint256`.

---

## Deployment

### Pre-Deployment Checklist

- [ ] Contract inherits `ZamaEthereumConfig`
- [ ] All FHE operations tested on Hardhat mock
- [ ] All ACL patterns verified
- [ ] No `view` modifier on FHE functions
- [ ] Security checklist completed

### Workflow

```bash
# 1. Deploy to Sepolia
npx hardhat run scripts/deploy.ts --network sepolia

# 2. Verify
npx hardhat verify --network sepolia <ADDRESS> "TokenName" "SYM"

# 3. Test on Sepolia (mint → transfer → decrypt → unauthorized decrypt)

# 4. Deploy to mainnet
npx hardhat run scripts/deploy.ts --network mainnet
npx hardhat verify --network mainnet <ADDRESS> "TokenName" "SYM"
```

### Production Hardening

- Transfer ownership to a multisig (never single EOA in production)
- Monitor for failed FHE operations in transaction traces
- Verify contracts on block explorer

---

## Comprehensive Pre-Deploy Checklist

### FHE-Specific

- [ ] Every encrypted state update has `FHE.allowThis()` + `FHE.allow()`
- [ ] No `if/require/assert` on encrypted conditions — only `FHE.select()`
- [ ] No encrypted values in event parameters
- [ ] All external encrypted inputs validated with `FHE.fromExternal(handle, proof)`
- [ ] `FHE.isInitialized()` checked for potentially unset values
- [ ] No `view` modifier on functions with FHE operations
- [ ] Trivial encryptions not treated as secrets
- [ ] Gas consumption doesn't vary based on encrypted conditions
- [ ] Decryption only at intended reveal points
- [ ] HCU estimated for every function — none exceed 10M HCU
- [ ] Smallest encrypted types used where possible
- [ ] Scalar operations used where one operand is plaintext
- [ ] No unbounded loops with FHE operations
- [ ] `ZamaEthereumConfig` inherited

### Standard Solidity

- [ ] Reentrancy protection (CEI + `nonReentrant`)
- [ ] Access control on all privileged functions
- [ ] Input validation (zero address, zero amount, bounds)
- [ ] SafeERC20 for all token operations
- [ ] Token decimal handling — no hardcoded `1e18`
- [ ] Multiply before divide in all math
- [ ] Events emitted for every state change
- [ ] Oracle staleness + sanity checks if using price feeds
- [ ] Contract verified on block explorer

### Testing

- [ ] Happy path with valid inputs
- [ ] Insufficient balance → silent 0-transfer (no revert)
- [ ] Zero values, max values, uninitialized values
- [ ] ACL: owner/recipient can decrypt, contract can operate
- [ ] Access control: unauthorized callers revert
- [ ] Property tests: invariants hold across sequences
- [ ] Deployed and tested on Sepolia before mainnet
- [ ] Ownership transferred to multisig

---

## Source

- HCU costs: https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md
- Zama Documentation: https://docs.zama.ai/protocol
- OpenZeppelin Confidential Contracts: https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
