---
name: testing
description: Testing encrypted contracts with Hardhat and the FHEVM plugin. How to create encrypted inputs, decrypt values in tests, and verify ACL behavior.
---

# Testing Encrypted Contracts

## What You Probably Got Wrong

**You tried to assert on encrypted values directly.** `expect(balance).to.equal(100)` doesn't work — `balance` is an encrypted handle, not a number. You need to decrypt it in your test first.

**You skipped ACL testing.** The most common FHEVM bug is missing ACL permissions. If you don't test that unauthorized addresses get rejected, you'll ship broken access control.

**You only tested the happy path.** FHE contracts silently handle failures (via `FHE.select`). If a transfer fails because of insufficient balance, it transfers 0 — it doesn't revert. You need to verify the zero-transfer case explicitly.

---

## Setup

### Hardhat Configuration

```typescript
// hardhat.config.ts
import "@fhevm/hardhat-plugin";

const config: HardhatUserConfig = {
  solidity: "0.8.24",
  // FHEVM plugin automatically configures the FHE environment
};
```

### Test File Structure

```typescript
import { ethers } from "hardhat";
import { fhevm } from "hardhat";

describe("ConfidentialERC20", function () {
  let contract: ConfidentialERC20;
  let alice: SignerWithAddress;
  let bob: SignerWithAddress;

  beforeEach(async function () {
    [alice, bob] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("ConfidentialERC20");
    contract = await Factory.deploy("Confidential Token", "CONF");
  });
});
```

---

## Creating Encrypted Inputs

Users encrypt values client-side before submitting. In tests, use `fhevm.createEncryptedInput()`:

```typescript
// Create an encrypted uint64 input
const input = fhevm.createEncryptedInput(
  await contract.getAddress(),  // Contract address
  alice.address                  // Sender address
);
input.add64(100n);  // The plaintext value to encrypt
const encrypted = await input.encrypt();

// Use in contract call
await contract.transfer(
  bob.address,
  encrypted.handles[0],    // externalEuint64 handle
  encrypted.inputProof     // ZK proof
);
```

### Multiple Inputs

```typescript
const input = fhevm.createEncryptedInput(
  await contract.getAddress(),
  alice.address
);
input.addBool(true);   // index 0 — externalEbool
input.add64(500n);     // index 1 — externalEuint64
input.add8(3);         // index 2 — externalEuint8
const encrypted = await input.encrypt();

await contract.multiInput(
  encrypted.handles[0],  // bool
  encrypted.handles[1],  // uint64
  encrypted.handles[2],  // uint8
  encrypted.inputProof   // single proof for all
);
```

---

## Decrypting Values in Tests

Encrypted values are handles. To verify correctness, decrypt them in tests:

```typescript
it("should have correct balance after mint", async function () {
  await contract.mint(1000n);

  // Get the encrypted balance handle
  const encryptedBalance = await contract.balanceOf(alice.address);

  // Decrypt it for assertion
  const balance = await fhevm.decrypt64(encryptedBalance);
  expect(balance).to.equal(1000n);
});
```

### Decryption Helpers

```typescript
// Different types have different decrypt functions
const boolVal = await fhevm.decryptBool(encryptedBool);
const uint8Val = await fhevm.decrypt8(encryptedUint8);
const uint16Val = await fhevm.decrypt16(encryptedUint16);
const uint32Val = await fhevm.decrypt32(encryptedUint32);
const uint64Val = await fhevm.decrypt64(encryptedUint64);
const addressVal = await fhevm.decryptAddress(encryptedAddr);
```

---

## What to Test

### 1. Basic Operations

```typescript
it("should transfer encrypted amount", async function () {
  await contract.mint(1000n);

  const input = fhevm.createEncryptedInput(
    await contract.getAddress(),
    alice.address
  );
  input.add64(300n);
  const encrypted = await input.encrypt();

  await contract.transfer(
    bob.address,
    encrypted.handles[0],
    encrypted.inputProof
  );

  // Verify both balances
  const aliceBalance = await fhevm.decrypt64(
    await contract.balanceOf(alice.address)
  );
  const bobBalance = await fhevm.decrypt64(
    await contract.balanceOf(bob.address)
  );

  expect(aliceBalance).to.equal(700n);
  expect(bobBalance).to.equal(300n);
});
```

### 2. Insufficient Balance (Silent Failure)

```typescript
it("should transfer 0 when balance is insufficient", async function () {
  await contract.mint(100n);

  const input = fhevm.createEncryptedInput(
    await contract.getAddress(),
    alice.address
  );
  input.add64(200n); // More than balance
  const encrypted = await input.encrypt();

  // This does NOT revert — it silently transfers 0
  await contract.transfer(
    bob.address,
    encrypted.handles[0],
    encrypted.inputProof
  );

  const aliceBalance = await fhevm.decrypt64(
    await contract.balanceOf(alice.address)
  );
  const bobBalance = await fhevm.decrypt64(
    await contract.balanceOf(bob.address)
  );

  // Balances unchanged — transfer was 0
  expect(aliceBalance).to.equal(100n);
  expect(bobBalance).to.equal(0n);
});
```

### 3. ACL Verification

```typescript
it("should allow owner to decrypt their balance", async function () {
  await contract.mint(1000n);

  // Alice (owner) should be able to decrypt
  const balance = await contract.balanceOf(alice.address);
  const decrypted = await fhevm.decrypt64(balance);
  expect(decrypted).to.equal(1000n);
});

it("should grant recipient access after transfer", async function () {
  await contract.mint(1000n);

  const input = fhevm.createEncryptedInput(
    await contract.getAddress(),
    alice.address
  );
  input.add64(500n);
  const encrypted = await input.encrypt();

  await contract.transfer(
    bob.address,
    encrypted.handles[0],
    encrypted.inputProof
  );

  // Bob should now be able to decrypt his balance
  const bobBalance = await contract.connect(bob).balanceOf(bob.address);
  const decrypted = await fhevm.decrypt64(bobBalance);
  expect(decrypted).to.equal(500n);
});
```

### 4. Edge Cases

```typescript
it("should handle zero transfer", async function () {
  await contract.mint(1000n);

  const input = fhevm.createEncryptedInput(
    await contract.getAddress(),
    alice.address
  );
  input.add64(0n);
  const encrypted = await input.encrypt();

  await contract.transfer(
    bob.address,
    encrypted.handles[0],
    encrypted.inputProof
  );

  const aliceBalance = await fhevm.decrypt64(
    await contract.balanceOf(alice.address)
  );
  expect(aliceBalance).to.equal(1000n);
});

it("should handle uninitialized balance", async function () {
  // Bob has never received tokens
  const bobBalance = await contract.balanceOf(bob.address);
  // Depending on implementation, this may be an uninitialized handle
  // Test that operations on it don't break
});
```

---

## What NOT to Test

- **FHE math correctness** — `FHE.add(3, 4)` returning 7 is Zama's responsibility, not yours
- **Coprocessor internals** — you're testing your contract logic, not the FHE engine
- **ACL contract internals** — test that YOUR permissions are set correctly, not that the ACL contract works

**DO test:** your contract's logic, ACL grants, edge cases, silent failure paths, and state transitions.

---

## Testing Checklist

- [ ] Happy path: basic operations with valid inputs
- [ ] Insufficient balance: verify silent 0-transfer (no revert)
- [ ] Zero values: transfer 0, deposit 0, etc.
- [ ] ACL: owner can decrypt, recipient gets access, unauthorized can't decrypt
- [ ] Uninitialized values: operations on addresses that haven't interacted
- [ ] Multiple operations: sequential transfers, multiple votes, etc.
- [ ] Input validation: `FHE.fromExternal()` with valid proofs
