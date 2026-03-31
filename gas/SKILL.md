---
name: gas
description: FHE gas costs (Homomorphic Complexity Units / HCU) for every encrypted operation and type. Use when optimizing contracts, estimating costs, or hitting the HCU limit. The preferred term is "FHE gas" — HCU is the formal unit.
---

# FHE Gas (Homomorphic Complexity Units)

## What You Probably Got Wrong

**You think FHE operations cost regular gas.** They don't. FHE operations are metered separately using **Homomorphic Complexity Units (HCU)**. A single `FHE.mul(euint64, euint64)` costs **596,000 HCU** — and the per-transaction limit is **20,000,000 HCU**. That's about 33 multiplications before your transaction reverts.

**You used euint256 when euint64 would work.** Larger types cost dramatically more HCU. An `add` on euint8 costs 88,000 HCU. On euint128 it costs 259,000 HCU — 3x more. Use the smallest type that fits your value range.

**You didn't know about the depth limit.** There are TWO HCU limits per transaction:
- **Global limit: 20,000,000 HCU** — total FHE computation
- **Depth limit: 5,000,000 HCU** — sequential operations (operations that depend on each other's output)

If either limit is exceeded, the transaction **reverts**.

**You wrote a loop over encrypted values.** Even a `for` loop with 10 iterations doing `FHE.add` on euint64 costs 1,620,000 HCU (10 × 162,000). A loop of 20 iterations with a comparison + select = 20 × (152,000 + 55,000) = 4,140,000 HCU. You're already at the depth limit.

---

## HCU Limits

| Limit | Value | What Happens |
|-------|-------|-------------|
| Global HCU per transaction | **20,000,000** | Transaction reverts if exceeded |
| Sequential depth HCU per transaction | **5,000,000** | Transaction reverts if exceeded |

**If you hit the limit:**
1. Refactor to reduce FHE operations
2. Split operations across multiple transactions
3. Use smaller encrypted types
4. Replace encrypted math with plaintext where privacy isn't needed

---

## Quick Reference: Common Operations on euint64

These are the most common operations (euint64 is the default type for balances):

| Operation | Scalar HCU | Non-scalar HCU | Budget at 20M limit |
|-----------|-----------|----------------|---------------------|
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
**Non-scalar** = both operands are encrypted (e.g., `FHE.add(encrypted1, encrypted2)`).

---

## Full HCU Cost Tables

### Boolean (`ebool`)

| Operation | Scalar | Non-scalar |
|-----------|--------|-----------|
| `and` | 22,000 | 25,000 |
| `or` | 22,000 | 24,000 |
| `xor` | 2,000 | 22,000 |
| `not` | — | 2 |
| `select` | — | 55,000 |
| `randEbool` | — | 19,000 |

### euint8

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

### euint16

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

### euint32

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

### euint64

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

### euint128

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

### euint256 (Limited Operations)

Only bitwise, shift, comparison, and select operations are available:

| Operation | Scalar | Non-scalar |
|-----------|--------|-----------|
| `and` / `or` / `xor` | ~38-39K | ~38-39K |
| `shr` / `shl` | ~38-39K | ~369-378K |
| `eq` / `ne` | ~117-118K | ~150-152K |
| `neg` | — | 269,000 |
| `not` | — | 130 |
| `select` | — | 108,000 |
| `randEuint256` | — | 30,000 |

**No `add`, `sub`, `mul`, `div` on euint256.** Use euint128 or smaller.

### eaddress (euint160 internally)

| Operation | Scalar | Non-scalar |
|-----------|--------|-----------|
| `eq` | 115,000 | 125,000 |
| `ne` | 115,000 | 124,000 |
| `select` | — | 83,000 |

### Misc Operations

| Operation | HCU |
|-----------|-----|
| `cast` | 32 |
| `trivialEncrypt` | 32 |
| `randBounded` | 23,000–30,000 |

---

## Optimization Patterns

### Use Scalar Operations When Possible

If one operand is a plaintext constant, use the scalar form — it's always cheaper:

```solidity
// ❌ More expensive — both operands encrypted
euint64 two = FHE.asEuint64(2);      // 32 HCU (trivial)
euint64 result = FHE.div(amount, two); // div not available for non-scalar!

// ✅ Cheaper — plaintext divisor
euint64 result = FHE.div(amount, 2);  // 715,000 HCU (scalar)
```

### Use the Smallest Type

```solidity
// ❌ Wasteful — euint64 add costs 162,000 HCU
euint64 count = FHE.add(count64, FHE.asEuint64(1));

// ✅ Efficient — euint8 add costs 88,000 HCU (46% cheaper)
euint8 count = FHE.add(count8, FHE.asEuint8(1));
```

**Type selection guide:**
| Value range | Type | add HCU |
|-------------|------|---------|
| 0–255 | euint8 | 88,000 |
| 0–65,535 | euint16 | 93,000 |
| 0–4.2B | euint32 | 125,000 |
| 0–18.4Q | euint64 | 162,000 |
| Larger | euint128 | 259,000 |

### Minimize Encrypted Operations

```solidity
// ❌ 3 FHE operations: add + gt + select = 162K + 152K + 55K = 369K HCU
euint64 newBal = FHE.add(balances[to], amount);
ebool check = FHE.gt(newBal, FHE.asEuint64(0));
euint64 result = FHE.select(check, newBal, balances[to]);

// ✅ If the check is always true by design, skip it: 162K HCU
euint64 newBal = FHE.add(balances[to], amount);
```

### Avoid Loops Over Encrypted Values

```solidity
// ❌ 10 iterations × (add + gt + select) = 10 × 369K = 3,690,000 HCU
// Close to the depth limit!
for (uint i = 0; i < 10; i++) {
    result = FHE.add(result, values[i]);
    ebool check = FHE.gt(result, threshold);
    result = FHE.select(check, result, threshold);
}

// ✅ Restructure: batch add first, then one comparison
for (uint i = 0; i < 10; i++) {
    result = FHE.add(result, values[i]);  // 10 × 162K = 1,620K HCU
}
// One final check
result = FHE.min(result, threshold);      // 219K HCU
// Total: 1,839K vs 3,690K
```

### Pre-compute Where Possible

If you can compute part of the logic with plaintext values, do it before encrypting:

```solidity
// ❌ 3 encrypted multiplications = 3 × 596K = 1,788K HCU
euint64 a = FHE.mul(price, quantity);
euint64 b = FHE.mul(a, FHE.asEuint64(feeBps));
euint64 fee = FHE.div(b, 10000);

// ✅ Combine plaintext constants: 1 encrypted mul + 1 div = 596K + 715K = 1,311K HCU
// If feeBps is a plaintext constant, use scalar mul
euint64 total = FHE.mul(price, quantity);  // 596K (non-scalar)
euint64 fee = FHE.div(total, 10000 / feeBps);  // 715K (scalar div)
```

---

## Estimating HCU for a Transaction

**Example: Confidential ERC-20 transfer**

```solidity
function transfer(address to, externalEuint64 amount, bytes calldata proof) external {
    euint64 amt = FHE.fromExternal(amount, proof);           // ~0 HCU (input validation)
    ebool canTransfer = FHE.le(amt, balances[msg.sender]);   // 149,000 HCU
    euint64 transferAmt = FHE.select(canTransfer, amt,
                          FHE.asEuint64(0));                  // 55,000 HCU + 32 HCU
    balances[msg.sender] = FHE.sub(balances[msg.sender],
                           transferAmt);                      // 162,000 HCU
    balances[to] = FHE.add(balances[to], transferAmt);       // 162,000 HCU
    // ACL grants...
}
// Total: ~528,000 HCU — well within the 20M limit
// A transfer uses ~2.6% of the global budget
```

**This means you can fit ~37 independent transfers worth of FHE computation in a single transaction** (though you'd never do this — each transfer is its own tx).

---

## Monitoring HCU Usage

If your transaction reverts with no clear reason, you may have hit the HCU limit. To debug:

1. **Count your FHE operations** — add up the HCU from the tables above
2. **Check the depth** — sequential operations (where output feeds into the next input) count toward the depth limit
3. **Use smaller types** — if you're close to the limit, downsize from euint64 to euint32 where possible
4. **Split transactions** — if one transaction does too much FHE work, split it into two

---

## Source

HCU costs sourced from: https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md
