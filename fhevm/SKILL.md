---
name: fhevm
description: The core FHEVM library — encrypted types, FHE operations, type casting, random number generation. The API reference that LLMs need to write correct encrypted Solidity.
---

# FHEVM — The Core Library

## What You Probably Got Wrong

**You used `euint256` for everything.** `euint64` is the standard type for balances and amounts in FHEVM. Larger types cost more gas for every operation. Use the smallest type that fits your data.

**You tried `FHE.div(a, b)` where `b` is encrypted.** Division and remainder only work with plaintext divisors. This is a fundamental limitation of the current FHE scheme — not a bug, not something that will be fixed soon.

**You marked FHE functions as `view`.** FHE operations change state (they interact with the coprocessor). Even `FHE.add(a, b)` is a state-changing operation. Remove `view` from any function that performs FHE operations.

**You confused `FHE.asEuint64(100)` with real encryption.** Trivial encryption wraps a plaintext value — everyone can see it. It's for constants and defaults, not secrets.

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
| `euint256` | Encrypted 256-bit uint | Full precision (expensive) |
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

**Critical:** `FHE.div()` and `FHE.rem()` only accept plaintext (non-encrypted) divisors. `FHE.div(a, encryptedB)` does not exist and will not compile.

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

**Critical:** `FHE.randEuint8(100)` is WRONG. The upper bound must be a power of 2. Use `FHE.randEuint8(128)` for values 0-127.

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
// Check if an encrypted value has been set
if (!FHE.isInitialized(value)) {
    value = FHE.asEuint64(0); // Default to encrypted zero
}
```

Always check `FHE.isInitialized()` before operating on values that might not have been set (e.g., balances for addresses that haven't received tokens yet).

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
    // ...
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

Comparing an encrypted value with a plaintext constant is efficient and common:

```solidity
ebool isPositive = FHE.gt(encryptedValue, 0);        // encValue > 0
ebool isMax = FHE.eq(encryptedValue, type(uint64).max);
euint64 capped = FHE.min(encryptedValue, 1000);      // Cap at 1000
```

---

## Common Pitfalls

### 1. FHE Functions Marked as `view`

```solidity
// ❌ WRONG — FHE operations are state-changing
function compute() public view returns (euint64) {
    return FHE.add(a, b); // ERROR: state mutability
}

// ✅ CORRECT
function compute() public returns (euint64) {
    return FHE.add(a, b);
}
```

### 2. Encrypted Divisors

```solidity
// ❌ WRONG — divisor must be plaintext
euint64 result = FHE.div(a, encryptedDivisor);

// ✅ CORRECT
euint64 result = FHE.div(a, 10);
```

### 3. Non-Power-of-2 Random Bounds

```solidity
// ❌ WRONG — must be power of 2
euint8 random = FHE.randEuint8(100);

// ✅ CORRECT
euint8 random = FHE.randEuint8(128); // 2^7 = 128
```

### 4. Branching on Encrypted Values

```solidity
// ❌ WRONG — can't use ebool in if/require
if (FHE.gt(balance, amount)) { ... }
require(FHE.gt(balance, amount), "Insufficient");

// ✅ CORRECT — use FHE.select
ebool sufficient = FHE.gt(balance, amount);
euint64 value = FHE.select(sufficient, amount, FHE.asEuint64(0));
```

### 5. Confusing Trivial and Real Encryption

```solidity
// ❌ MISLEADING — value 42 is visible to everyone onchain
euint64 "secret" = FHE.asEuint64(42);

// ✅ CORRECT — real secret comes from user input
euint64 secret = FHE.fromExternal(externalHandle, proof);
```
