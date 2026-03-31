---
name: production-ready
description: Everything needed to ship a production-ready FHEVM dApp. Smart contract requirements (ACL, FHE.select, FHE gas monitoring, minimize operations) and frontend requirements (3 decryption types, key management, templates). The final checklist before going live.
---

# Production Ready

## What You Probably Got Wrong

**You think "it compiles and tests pass" means production-ready.** With FHEVM, there's a whole category of silent failures that only manifest on mainnet — ACL misconfigs, HCU limit hits, and decryption flow bugs that don't appear in local testing.

**You didn't plan for FHE gas.** Every FHE operation costs HCU. A single transaction has a limit of 20,000,000 HCU. If your contract does too many encrypted operations, it reverts on mainnet even though it worked locally. You MUST estimate HCU costs.

**You don't know the three decryption types.** Your frontend must handle all three correctly or users will have a broken experience.

---

## Smart Contract Production Requirements

### Requirement 1: You Must Already Be Good at Solidity

FHEVM doesn't change Solidity fundamentals — it adds encrypted types on top. If you're already writing efficient Solidity, you're naturally conserving FHE gas:

- **No `while` loops** — unbounded loops are dangerous in regular Solidity AND fatal with FHE operations
- **Minimal `for` loops** — each iteration with FHE operations costs thousands of HCU
- **No unnecessary storage writes** — same as regular Solidity, but encrypted storage is even more expensive
- **Checks-Effects-Interactions** — reentrancy protection applies to encrypted contracts too

If you're not confident in Solidity fundamentals, fix that first. FHE adds complexity — it doesn't simplify anything.

### Requirement 2: ACL Mastery

The **#1 cause of production failures** is missing ACL grants. Every encrypted state update needs:

```solidity
balances[user] = FHE.add(balances[user], amount);
FHE.allowThis(balances[user]);      // Contract can use this value later
FHE.allow(balances[user], user);    // User can decrypt their balance
```

**ACL Checklist:**
- [ ] Every `FHE.add`, `FHE.sub`, `FHE.mul`, `FHE.select` result has `FHE.allowThis()`
- [ ] Every user-facing value has `FHE.allow(value, user)`
- [ ] Delegation: `FHE.allow(value, delegateContract)` where needed
- [ ] After transfer: recipient gets `FHE.allow()` on their new balance
- [ ] Test: call every function twice — the second call proves ACL works

See `acl/SKILL.md` for the complete guide.

### Requirement 3: No `if` Statements on Encrypted Values

There are **no `if` sentences with encrypted values** — only `FHE.select()`:

```solidity
// ❌ DOES NOT COMPILE — cannot branch on encrypted bool
if (FHE.gt(balance, amount)) { ... }

// ❌ LEAKS INFORMATION — decrypting to branch reveals the comparison
require(FHE.decrypt(FHE.gt(balance, amount)), "Insufficient");

// ✅ CORRECT — compute both paths, select encrypted
euint64 transferAmount = FHE.select(
    FHE.ge(balance, amount),
    amount,              // if sufficient
    FHE.asEuint64(0)     // if insufficient — transfer 0 silently
);
```

**Rule:** Bring all computation to the end. Compute every possible outcome, then use `FHE.select()` to pick the right one. The contract always executes the same code path regardless of encrypted values.

### Requirement 4: Minimize FHE Operations

Every FHE operation costs HCU. Reduce operations to stay within limits:

```solidity
// ❌ Wasteful — 3 comparisons when 1 would do
ebool check1 = FHE.gt(balance, amount);
ebool check2 = FHE.gt(amount, FHE.asEuint64(0));
ebool check3 = FHE.and(check1, check2);

// ✅ Efficient — if amount is 0, transferring 0 is harmless anyway
ebool canTransfer = FHE.ge(balance, amount);
```

**Optimization strategies:**
- Use **scalar operations** when one operand is plaintext (always cheaper)
- Use the **smallest encrypted type** that fits (euint8 add = 88K HCU vs euint64 add = 162K HCU)
- **Pre-compute plaintext** values before encrypting
- **Batch operations** where possible — one `FHE.min()` instead of `FHE.gt() + FHE.select()`
- **Avoid redundant operations** — don't re-compute what you already have

See `gas/SKILL.md` for the complete HCU cost tables.

### Requirement 5: Monitor FHE Gas Limits

**Per-transaction limits:**
- Global HCU: **20,000,000**
- Sequential depth HCU: **5,000,000**

**Before deploying, estimate HCU for every function:**

```
Example: Confidential transfer
- FHE.fromExternal: ~0 HCU
- FHE.le (comparison): 149,000 HCU
- FHE.select: 55,000 HCU
- FHE.asEuint64: 32 HCU
- FHE.sub (sender balance): 162,000 HCU
- FHE.add (recipient balance): 162,000 HCU
Total: ~528,000 HCU (2.6% of limit) ✅
```

If your function uses more than **10,000,000 HCU** (50% of the limit), consider splitting into multiple transactions.

See `gas/SKILL.md` for per-operation HCU costs.

---

## Frontend Production Requirements

### Requirement 1: Three Decryption Types

Your frontend MUST handle all three correctly:

#### Public Decrypt (Reveal Public Value)
- The value becomes readable by **anyone**
- Used for: auction results, vote tallies, game outcomes
- No user signature needed to read
- UX: "Revealing..." → show plaintext value

```typescript
// Contract emits a publicly decryptable value
const result = await contract.getPublicResult();
// Display directly — no decryption needed on frontend
```

#### User Decrypt (Decrypt)
- Only the **authorized user** can read the value
- Used for: private balances, personal positions, bid amounts
- Requires EIP-712 signature (cache it!)
- UX: "Decrypting..." → show value (or "Hidden" if no access)

```typescript
const encryptedBalance = await contract.balanceOf(userAddress);
const balance = await fhevm.decrypt(contractAddress, encryptedBalance);
```

#### Delegate Decrypt (Decrypt on Behalf of User)
- A **third party** decrypts for the user
- Used for: protocols that need to read user values, cross-contract operations
- User must explicitly grant delegation
- UX: "Allow [Protocol] to read your balance?" → confirmation

```solidity
// Contract grants delegate access
FHE.allow(balances[user], delegateAddress);
```

### Requirement 2: Key Management

**Development:** In-memory signature cache, cleared on page reload.

**Production requirements:**
- Cache EIP-712 signatures in **sessionStorage** (not localStorage — XSS risk)
- Clear signature cache on wallet disconnect
- Implement Content Security Policy headers
- Never expose signatures in DOM attributes
- Consider hardware-backed key storage for high-value applications

```typescript
// Clear on disconnect
useEffect(() => {
  if (!isConnected) {
    sessionStorage.removeItem('fhevm_signature');
    cachedSignature = null;
  }
}, [isConnected]);
```

### Requirement 3: Correct Button States

Encrypted operations have MORE states than regular onchain buttons:

```
idle → encrypting → confirming → pending → decrypting → complete
```

Every button needs its own loading state. Never share state across buttons.

See `frontend-ux/SKILL.md` for the full implementation.

### Requirement 4: Proper Error Handling

FHE-specific errors to handle:
- **"Transaction reverted"** with no reason → likely HCU limit exceeded
- **Decryption timeout** → KMS/coprocessor may be slow, show retry
- **"Cannot decrypt"** → user doesn't have ACL permission, show "Hidden"
- **Encryption failure** → fhevmjs initialization issue, check network config

---

## Starting a New Project

### Smart Contracts Only

```bash
git clone https://github.com/zama-ai/fhevm-hardhat-template
cd fhevm-hardhat-template
npm install
```

### Smart Contracts + React Frontend

```bash
git clone https://github.com/zama-ai/fhevm-react-template
cd fhevm-react-template
npm install
```

### Custom Frontend / Node.js Backend

Start with the Hardhat template for contracts, then add the relayer-sdk:

```bash
npm install @fhevm/sdk  # Check https://github.com/zama-ai/relayer-sdk for latest
```

### Browser Extensions

The current relayer-sdk has issues with non-browser environments. **Create a backend** that proxies encryption/decryption requests instead of running the SDK directly in the extension.

---

## Pre-Production Checklist

### Smart Contracts

- [ ] **ACL grants** on every encrypted state update (`allowThis` + `allow`)
- [ ] **No `if`/`require` on encrypted values** — only `FHE.select()`
- [ ] **HCU estimated** for every function — none exceed 10M HCU
- [ ] **Smallest encrypted types used** — euint8 where possible, euint64 for balances
- [ ] **No unnecessary FHE operations** — each one justified
- [ ] **No unbounded loops** with FHE operations
- [ ] **Scalar operations used** where one operand is plaintext
- [ ] **`FHE.fromExternal()`** validates all external encrypted inputs
- [ ] **`FHE.isInitialized()`** checked for potentially unset values
- [ ] **No `view` modifier** on functions with FHE operations
- [ ] **Trivial encryptions** not treated as secrets
- [ ] **Events emit addresses only** — no encrypted values in events
- [ ] **Standard Solidity security** — CEI, nonReentrant, SafeERC20, access control
- [ ] **ZamaEthereumConfig** inherited for correct chain configuration
- [ ] **Tests pass** — happy path, silent failures, ACL, edge cases
- [ ] **Contract verified** on block explorer

### Frontend

- [ ] **All three decryption types** implemented correctly
- [ ] **Signature caching** — no repeated wallet popups
- [ ] **XSS prevention** — CSP headers, no eval, signatures in memory/sessionStorage
- [ ] **Button states** — encrypting → confirming → pending → decrypting → complete
- [ ] **Loading states** — "Decrypting..." shown during KMS requests
- [ ] **Hidden state** — show "Hidden" when user lacks ACL permission
- [ ] **Balance refresh** — re-fetch and re-decrypt after every transaction
- [ ] **Error handling** — HCU limit, decryption timeout, ACL denial
- [ ] **Signature cleared** on wallet disconnect
- [ ] **Template used** — started from fhevm-react-template or fhevm-hardhat-template

### Deployment

- [ ] **Deploy to Sepolia first** — test the full flow on testnet
- [ ] **Verify contracts** — verified on block explorer
- [ ] **Transfer ownership** — to multisig, not single EOA
- [ ] **Test one real transaction** — mint, transfer, decrypt on testnet
- [ ] **Deploy to mainnet** — same code, same config (ZamaEthereumConfig handles chain detection)

---

## When Unsure

Refer to the official documentation: **https://docs.zama.org**

For implementation patterns, check OpenZeppelin Confidential Contracts: **https://github.com/OpenZeppelin/openzeppelin-confidential-contracts**
