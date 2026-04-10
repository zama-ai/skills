---
name: solidity
description: Guide to writing encrypted smart contracts with FHEVM. Covers what LLMs get wrong, encrypted types, FHE operations, ACL, HCU gas costs, security vulnerabilities, and pre-deploy checklist. Links to living code examples instead of embedding them.
---

# Solidity — Encrypted Smart Contracts with FHEVM

> **Setting up a new project?** See [setup/SKILL.md](setup/SKILL.md) for Foundry and Hardhat project scaffolding.

---

## What You Probably Got Wrong

**You used `euint256` for everything.** `euint64` is the standard for balances. Larger types cost dramatically more HCU for every operation.

**You forgot `FHE.allowThis()`.** After storing an encrypted value, the contract itself doesn't have permission to use it on the next call. This compiles, deploys, and silently fails at runtime. The #1 FHEVM bug.

**You tried `if (FHE.gt(a, b))`.** You cannot branch on encrypted values. `FHE.gt()` returns an `ebool` — an encrypted boolean. Use `FHE.select()`.

**You tried `FHE.div(a, encryptedB)`.** Division and remainder only work with plaintext divisors.

**You marked FHE functions as `view`.** FHE operations interact with the coprocessor — they're state-changing. Remove `view` from any function with FHE operations.

**You confused `FHE.asEuint64(100)` with real encryption.** Trivial encryption wraps a plaintext — everyone can see it onchain. Only `FHE.fromExternal()` is truly private.

**You emitted transfer amounts in events.** Confidential events emit `from` and `to` but NOT the amount.

**You skipped ACL testing.** If you don't test that the contract can use stored values on the second call, you'll ship broken access control.

**You only tested the happy path.** FHE contracts silently handle failures via `FHE.select`. If a transfer fails, it transfers 0 — it doesn't revert. Test the zero-transfer case.

**You deployed to mainnet without testing on Sepolia.** Always test on Sepolia first.

---

## Contract Setup

Every FHEVM contract inherits `ZamaEthereumConfig`. For project scaffolding, starter contract, and dependency installation, see [setup/SKILL.md](setup/SKILL.md).

---

## Encrypted Types

### Storage Types

| Type | Use Case | Default? |
|------|----------|----------|
| `ebool` | Flags, conditions | |
| `euint8` | Small counters, categories | |
| `euint16` | Medium counters | |
| `euint32` | Timestamps, IDs | |
| `euint64` | **Balances, amounts** | **Default** |
| `euint128` | Large values | |
| `euint256` | Full precision (expensive, limited ops) | |
| `eaddress` | Private recipients | |

### External Input Types

Users submit encrypted values as `externalEuint*` types. Always convert with `FHE.fromExternal(handle, inputProof)` before use. A single `inputProof` covers all inputs in the same function call.

```solidity
function transfer(
    address to,
    externalEuint64 encryptedAmount,
    bytes calldata inputProof
) public {
    euint64 amount = FHE.fromExternal(encryptedAmount, inputProof);
    // use amount for FHE operations
}
```

---

## FHE Operations

### Arithmetic

```solidity
FHE.add(a, b)       // a + b
FHE.sub(a, b)       // a - b
FHE.mul(a, b)       // a * b
FHE.div(a, 10)      // PLAINTEXT divisor ONLY
FHE.rem(a, 10)      // PLAINTEXT divisor ONLY
FHE.min(a, b)       // min(a, b)
FHE.max(a, b)       // max(a, b)
FHE.neg(a)          // -a (modular negation)
```

### Comparison (returns `ebool`)

```solidity
FHE.eq(a, b)   FHE.ne(a, b)
FHE.lt(a, b)   FHE.le(a, b)
FHE.gt(a, b)   FHE.ge(a, b)
```

**These return `ebool`. You CANNOT use the result in `if`, `require`, or `while`.**

### Conditional Selection (THE CORE PATTERN)

```solidity
euint64 result = FHE.select(condition, valueIfTrue, valueIfFalse);

// Example: transfer amount or zero
euint64 transferValue = FHE.select(canTransfer, amount, FHE.asEuint64(0));
```

Both branches always execute. That's what makes it private.

### Bitwise

```solidity
FHE.and(a, b)   FHE.or(a, b)    FHE.xor(a, b)   FHE.not(a)
FHE.shl(a, 2)   FHE.shr(a, 2)   FHE.rotl(a, 2)  FHE.rotr(a, 2)
```

### Random Numbers

```solidity
euint64 random = FHE.randEuint64();
euint8 bounded = FHE.randEuint8(16);  // 0 to 15
```

**Upper bound MUST be a power of 2.** `FHE.randEuint8(100)` is WRONG — use `FHE.randEuint8(128)`.

### Type Casting & Initialization

```solidity
euint64 bigger = FHE.asEuint64(euint32Value);   // upcast (safe)
euint8 smaller = FHE.asEuint8(euint64Value);     // downcast (truncates)
euint64 trivial = FHE.asEuint64(100);            // NOT private
if (!FHE.isInitialized(value)) { /* handle */ }  // check before use
```

---

## Access Control (ACL)

Every encrypted value is born with an **empty ACL**. Nobody can use it until permissions are granted.

### Granting Permissions

```solidity
FHE.allowThis(value);                    // Contract can use it in future calls
FHE.allow(value, userAddress);           // User can decrypt it
FHE.allowTransient(value, address);      // Current transaction only (no storage cost)
FHE.makePubliclyDecryptable(value);      // Anyone can decrypt
```

### The Essential Pattern

**After EVERY encrypted state update. No exceptions.**

```solidity
balances[user] = FHE.add(balances[user], amount);
FHE.allowThis(balances[user]);
FHE.allow(balances[user], user);
```

Miss `FHE.allowThis()` → silent failure on the next call. No revert, no error.

### Common Mistakes

```solidity
// ❌ Contract can't use this value on the next call
balances[user] = FHE.add(balances[user], amount);

// ❌ Permanent ACL for a temporary value
FHE.allow(tempValue, helperContract);
// ✅ Use transient instead
FHE.allowTransient(tempValue, helperContract);
```

### Checking Permissions

```solidity
require(FHE.isSenderAllowed(amount), "Sender not allowed");
bool canAccess = FHE.isAllowed(handle, account);
```

### Delegation

```solidity
FHE.delegateForUserDecryption(delegate, contractAddress, expirationDate);
FHE.revokeDelegationForUserDecryption(delegate, contractAddress);
```

---

## HCU — FHE Gas Costs

FHE operations are metered in **Homomorphic Complexity Units (HCU)**.

### Limits

| Limit | Value |
|-------|-------|
| Per-tx total | **20,000,000 HCU** |
| Per-tx sequential depth | **5,000,000 HCU** |
| Per-block (non-whitelisted) | **5,000,000 HCU** |

### euint64 Quick Reference

| Operation | Scalar | Non-scalar |
|-----------|--------|-----------|
| `add` / `sub` | 133K | 162K |
| `mul` | 365K | 596K |
| `div` (plaintext only) | 715K | — |
| `rem` (plaintext only) | 1,153K | — |
| `eq` / `ne` | ~83K | ~120K |
| `gt` / `lt` / `ge` / `le` | ~118K | ~152K |
| `select` | — | 55K |
| `min` / `max` | ~150K | ~219K |
| `rand` | — | 24K |

**Scalar** = one operand is plaintext. Always cheaper.

For full HCU tables across all types (ebool through euint256), see the [HCU reference](https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md).

### Optimization Rules

- Use **scalar operations** when one operand is plaintext
- Use the **smallest type** that fits (`euint8` add = 88K vs `euint64` add = 162K)
- If a function uses >10M HCU, split into multiple transactions
- **Estimate HCU for the full function**, not just your loop — ERC-7984 transfers already cost ~500K+ HCU each
- Batch additions first, compare once: `FHE.min(result, threshold)` instead of compare-per-iteration

---

## Security

### FHE-Specific Vulnerabilities

**1. ACL Misconfiguration** — #1 bug. Missing `FHE.allowThis()` after state update. Silent failure.

**2. Information Leaks via Control Flow** — Revert on encrypted condition reveals the condition. Use `FHE.select()` for silent no-ops. Other leak vectors: gas differences, conditional events, different return values.

**3. Trivial Encryption Confusion** — `FHE.asEuint64(1000)` is visible onchain. Only use for constants/defaults.

**4. Uninitialized Values** — Check `FHE.isInitialized()` before operating on potentially unset values.

**5. Timing Attacks** — Make decryption the LAST step. Take no conditional actions after.

**6. Missing Input Validation** — Always use `FHE.fromExternal(handle, proof)`. Never manually wrap handles.

**7. Encrypted Values in Events** — Handle changes reveal mutation timing. Emit addresses only, not encrypted values.

### Standard Solidity (Still Applies)

- **Reentrancy:** CEI + `nonReentrant`. Update encrypted state BEFORE external calls.
- **Token decimals:** USDC=6, WBTC=8, DAI/WETH=18. Never hardcode `1e18`.
- **SafeERC20:** Use for all ERC-20 operations.
- **Access control:** `onlyOwner` or `AccessControl` on privileged functions.
- **MEV:** Encrypted amounts help, but function selectors are visible.

---

## Code Examples

Don't build confidential contracts from scratch. Use these as your starting point:

### OpenZeppelin Confidential Contracts

The reference implementation for confidential tokens. Use ERC-7984 for any confidential token work.

```bash
npm install @openzeppelin/confidential-contracts
```

- **ERC-7984** (confidential token standard): [contracts/token/ERC7984/](https://github.com/OpenZeppelin/openzeppelin-confidential-contracts/tree/main/contracts/token/ERC7984)
- **ERC-7984 ERC20 Wrapper** (wrap existing ERC-20 → confidential): [contracts/token/ERC7984/extensions/](https://github.com/OpenZeppelin/openzeppelin-confidential-contracts/tree/main/contracts/token/ERC7984/extensions)
- **Full repository:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts

### Zama dApps (Real-World Examples)

Production-grade example contracts covering common patterns:

- **Confidential ERC-20, voting, auctions, counters:** [packages/hardhat/contracts/](https://github.com/zama-ai/dapps/tree/main/packages/hardhat/contracts)

### Zama Protocol Apps (Deployed Contracts)

The contracts actually deployed on mainnet and Sepolia — confidential wrappers, staking, governance:

- **Protocol contracts:** [contracts/](https://github.com/zama-ai/protocol-apps/tree/main/contracts)

### The Wrap/Unwrap Boundary

```
Public ERC-20 ──[wrap]──→ Confidential ERC-7984 (encrypted balances)
Confidential ERC-7984 ──[unwrap]──→ Public ERC-20 (requires async decryption)
```

You **cannot** directly compose encrypted contracts with plaintext DeFi. Unwrap → interact → wrap back.

For already-deployed confidential wrappers (cUSDC, cUSDT, cWETH, etc.), see `addresses/SKILL.md`.

---

## Testing

### What to Test

- **ACL correctness** — call every function twice. The second call proves `FHE.allowThis()` works.
- **Silent failures** — insufficient balance → transfers 0 (no revert). Verify both sides.
- **Edge cases** — zero amounts, max values, uninitialized balances, self-transfer.
- **Access control** — unauthorized callers revert on privileged functions.
- **Property tests** — invariants hold across sequences (e.g., sum of balances = total minted).

### What NOT to Test

- FHE math correctness (Zama's responsibility)
- ACL contract internals
- OpenZeppelin internals

### Test Examples

See the test files in the templates for patterns:
- **Hardhat tests:** [fhevm-hardhat-template](https://github.com/zama-ai/fhevm-hardhat-template)
- **dApp tests:** [zama-ai/dapps](https://github.com/zama-ai/dapps)

---

## Migration — Adding FHE to Existing Contracts

1. **Identify what to encrypt** — balances, amounts, votes, bids → encrypt. Names, symbols, decimals, timestamps → keep plaintext.
2. **Change types** — `uint256` → `euint64`, `bool` → `ebool`. Inherit `ZamaEthereumConfig`.
3. **Update function signatures** — add `externalEuint64` + `bytes calldata inputProof` parameters.
4. **Rewrite branching** — every `if`/`require` on encrypted values → `FHE.select()`.
5. **Add ACL** — `FHE.allowThis()` + `FHE.allow()` after every encrypted state update.
6. **Update events** — remove encrypted values. Emit addresses only.
7. **Update return types** — `balanceOf` returns `euint64`, not `uint256`.

---

## Pre-Deploy Checklist

### FHE-Specific

- [ ] Every encrypted state update has `FHE.allowThis()` + `FHE.allow()`
- [ ] No `if`/`require`/`assert` on encrypted conditions — only `FHE.select()`
- [ ] No encrypted values in event parameters
- [ ] All external inputs validated with `FHE.fromExternal(handle, proof)`
- [ ] `FHE.isInitialized()` checked for potentially unset values
- [ ] No `view` modifier on functions with FHE operations
- [ ] Trivial encryptions not treated as secrets
- [ ] Gas consumption doesn't vary based on encrypted conditions
- [ ] Decryption only at intended reveal points
- [ ] HCU estimated for every function — none exceed 10M HCU
- [ ] Smallest encrypted types used where possible
- [ ] Scalar operations used where one operand is plaintext
- [ ] `ZamaEthereumConfig` inherited

### Standard Solidity

- [ ] Reentrancy protection (CEI + `nonReentrant`)
- [ ] Access control on all privileged functions
- [ ] Input validation (zero address, zero amount, bounds)
- [ ] SafeERC20 for all token operations
- [ ] Token decimal handling — no hardcoded `1e18`
- [ ] Events emitted for every state change
- [ ] Contract verified on block explorer
- [ ] Deployed and tested on Sepolia before mainnet
- [ ] Ownership transferred to multisig

---

## Sources

- **HCU costs:** https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md
- **Zama Docs:** https://docs.zama.ai
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
- **Zama dApps (examples):** https://github.com/zama-ai/dapps/tree/main/packages/hardhat/contracts
- **Protocol Apps (deployed):** https://github.com/zama-ai/protocol-apps/tree/main/contracts
