---
name: concepts
description: The essential mental models for building with encrypted computation — what LLMs get wrong and what humans need explained. "Nothing is plaintext" and "you cannot branch on secrets" are the core messages. Use when building encrypted contracts, designing a system with FHE, or when someone asks "how does encrypted computation actually work?"
---

# FHE Concepts

## What You Probably Got Wrong

**"I'll decrypt, check the condition, then re-encrypt."** No. The entire point of FHE is that you NEVER decrypt during computation. If you decrypt to check a condition, you've leaked the value to the blockchain — every node sees it. Decrypt only for final output, and only to authorized parties.

**"Encrypted values work like regular values."** No. You can't use `if`, `require`, `while`, or any control flow with encrypted values. You can't log them in events. You can't return them as plaintext. They exist in a parallel universe where only FHE operations work.

**"FHE is like ZK proofs."** No. ZK proves you know something without revealing it — one-time proof, no computation on the secret. FHE lets you compute on encrypted data — ongoing operations without ever decrypting. They solve different problems.

**"FHE operations are free like view functions."** No. Every FHE operation (add, multiply, compare) is a state-changing transaction that costs gas. The coprocessor does the heavy lifting offchain, but the onchain accounting still happens.

---

## Nothing Is Plaintext

**This is the most important concept in FHEVM. If you internalize nothing else, internalize this.**

### Encrypted Values Are Opaque

An encrypted value in FHEVM is a handle — an opaque reference to a ciphertext managed by the coprocessor. You cannot:

- Read its value (not even the contract that created it)
- Use it in `if`, `require`, `assert`, `while`
- Log it in events (the handle is meaningless to observers)
- Return it as a readable value to an unauthorized caller
- Compare it with `==`, `<`, `>` in Solidity

You CAN:
- Compute on it with FHE operations (`FHE.add`, `FHE.mul`, `FHE.gt`, etc.)
- Select between values based on encrypted conditions (`FHE.select`)
- Grant access to specific addresses (`FHE.allow`, `FHE.allowThis`)
- Make it publicly decryptable (`FHE.makePubliclyDecryptable`)
- Check if it's been initialized (`FHE.isInitialized`)

```
Encrypted value ──[FHE.add]──→ Encrypted result
                ──[FHE.gt]──→ Encrypted boolean
                ──[FHE.select]──→ Encrypted choice
                ──[FHE.allow]──→ Decryptable by specific address
                ──[makePubliclyDecryptable]──→ Decryptable by anyone
```

### The Branch Problem

This is where every LLM gets stuck on the first try:

```solidity
// REGULAR SOLIDITY — you check a condition and branch
if (balance >= amount) {
    // do the transfer
} else {
    // revert or skip
}

// FHEVM — YOU CANNOT DO THIS
// FHE.ge(balance, amount) returns an ebool — an ENCRYPTED boolean
// You can't use an encrypted boolean in an if statement
// The EVM doesn't know if it's true or false — that's the whole point
```

**The solution is `FHE.select()` — the encrypted ternary operator:**

```solidity
ebool canTransfer = FHE.le(amount, balance);

// If canTransfer is true: transferValue = amount
// If canTransfer is false: transferValue = 0
// Nobody knows which one it is — the computation happens encrypted
euint64 transferValue = FHE.select(canTransfer, amount, FHE.asEuint64(0));

// Both paths execute, but with either the real amount or zero
balance = FHE.sub(balance, transferValue);
recipientBalance = FHE.add(recipientBalance, transferValue);
```

**Both branches always execute.** That's what makes it private — an observer can't tell which branch was "taken" because both always run. The `FHE.select()` just determines which value is used.

### Information Leaks

Even with encrypted values, you can accidentally leak information:

```solidity
// ❌ LEAK — the revert itself reveals that balance < amount
require(FHE.decrypt(FHE.ge(balance, amount)), "Insufficient balance");

// ❌ LEAK — different gas costs for different branches reveal the path taken
if (somePublicCondition) {
    // do 3 FHE operations
} else {
    // do 1 FHE operation
}

// ❌ LEAK — emitting the encrypted value's handle in an event
// The handle changes when the value changes, so observers can track mutations
emit BalanceChanged(user, encryptedBalance); // handle leaks mutation info

// ✅ SAFE — emit only metadata, not encrypted values
emit Transfer(from, to); // addresses are public, amount is not
```

**The rule:** If your contract behaves differently (reverts, costs different gas, emits different events) based on an encrypted value, you've leaked information about that value.

---

## The ACL Mental Model

Every encrypted value is born with an empty access list. **Nobody can use it until permissions are explicitly granted.**

Think of it like a safe deposit box:
- The coprocessor holds the box (ciphertext)
- `FHE.allow(value, address)` gives someone a key to the box
- `FHE.allowThis(value)` gives the contract itself a key
- `FHE.allowTransient(value, address)` gives a temporary key that expires after the transaction
- Without a key, the value exists but is completely unusable

```
Created ──→ Empty ACL (nobody can use it)
         ──[FHE.allowThis()]──→ Contract can use it in future calls
         ──[FHE.allow(val, user)]──→ User can decrypt it
         ──[FHE.allowTransient(val, addr)]──→ Address can use it THIS TX ONLY
```

**The #1 bug in FHEVM development:** storing an encrypted value without calling `FHE.allowThis()`. On the next transaction, the contract tries to use the stored value and fails — it doesn't have permission to access its own data.

---

## Trivial vs Real Encryption

Two ways to create encrypted values — and they are NOT equivalent:

```solidity
// TRIVIAL ENCRYPTION — the value 100 is visible onchain to everyone
// This is for constants, defaults, and initial values
euint64 trivial = FHE.asEuint64(100);

// REAL ENCRYPTION — the value is encrypted client-side, invisible onchain
// This is for user secrets (balances, amounts, votes, bids)
euint64 real = FHE.fromExternal(externalHandle, inputProof);
```

**Trivial encryption is not private.** Anyone can see that `FHE.asEuint64(100)` is 100. Use it for:
- Default values (`FHE.asEuint64(0)`)
- Public constants in comparisons
- Initialization of encrypted accumulators

**Real encryption comes from users.** They encrypt values client-side using `fhevm.createEncryptedInput()`, submit the handle + proof, and the contract validates with `FHE.fromExternal()`.

---

## Teaching Your Human

### "Why can't I just encrypt everything?"
*"Every encrypted operation costs gas — FHE.add costs more than a regular addition because the coprocessor has to do the computation on ciphertexts. Encrypt only what needs to be private. Public values (token name, total supply, timestamps) should stay plaintext — they're cheaper and other contracts can read them directly."*

### "Why can't I use if/else?"
*"The EVM doesn't know if an encrypted boolean is true or false — that's the privacy guarantee. Instead, you use FHE.select(), which is like a ternary operator that works on encrypted conditions. Both branches always execute, so nobody can tell which path was 'really' taken."*

### "How is this different from ZK proofs?"
*"ZK proofs say 'I know a secret that satisfies this condition' without revealing the secret. It's a one-time proof. FHE says 'here's encrypted data — compute on it without ever seeing it.' FHE enables ongoing computation on secrets. ZK proves things about secrets. Different tools for different jobs."*

### "What about performance?"
*"FHE operations are slower than plaintext operations — that's the tradeoff for privacy. The FHEVM coprocessor handles the heavy math offchain, so you're not paying for raw FHE on the EVM. But encrypted operations still cost more gas than plaintext ones. Design your contracts to minimize the number of FHE operations — encrypt only what matters."*

### "Can the coprocessor see my data?"
*"The coprocessor performs computation on ciphertexts. It needs the evaluation key (which lets it compute on encrypted data) but NOT the decryption key. Only the Key Management Service (KMS) holds decryption keys, and decryption only happens when explicitly requested with proper ACL authorization."*

---

## Resources

- **Zama Documentation:** https://docs.zama.ai/protocol
- **FHEVM GitHub:** https://github.com/zama-ai/fhevm
- **FHEVM Solidity Library:** https://github.com/zama-ai/fhevm/tree/main/lib
- **FHESkills (for agents):** https://fheskills.com
