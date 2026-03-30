---
name: frontend
description: Handling encrypted state in your dApp UI — encrypting inputs client-side, pending decryption states, and displaying encrypted data to users.
---

# Frontend — Encrypted State in Your UI

## What You Probably Got Wrong

**You tried to display encrypted balances directly.** Encrypted values are opaque handles. You must decrypt them client-side before displaying — and only the authorized user can do that.

**You forgot the loading state for decryption.** Decryption is async. Between requesting decryption and getting the result, your UI needs a loading indicator. Unlike regular contract reads (instant), decryption goes through the KMS.

**You used `ethers.js` to read encrypted values like regular uints.** Encrypted return values from `balanceOf()` are handles, not numbers. You need the fhevmjs library to decrypt them.

---

## Client-Side Encryption

Users encrypt values in the browser before submitting transactions. The contract never sees plaintext.

### Using fhevmjs

```typescript
import { createInstance } from "fhevmjs";

// Initialize FHEVM instance (once, at app startup)
const fhevm = await createInstance({
  networkUrl: "https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY",
  gatewayUrl: "https://gateway.zama.ai",
});

// Create encrypted input for a contract call
const input = fhevm.createEncryptedInput(
  contractAddress,  // The contract that will receive the value
  userAddress       // The user sending the transaction
);
input.add64(1000);  // Encrypt the value 1000 as euint64
const encrypted = await input.encrypt();

// Submit transaction with encrypted values
const tx = await contract.transfer(
  recipientAddress,
  encrypted.handles[0],    // externalEuint64
  encrypted.inputProof     // ZK proof
);
```

### Multiple Encrypted Values

```typescript
const input = fhevm.createEncryptedInput(contractAddress, userAddress);
input.addBool(true);     // index 0
input.add64(500n);       // index 1
input.add8(3);           // index 2
const encrypted = await input.encrypt();

// Each handle corresponds to the order you added values
await contract.multiInput(
  encrypted.handles[0],  // externalEbool
  encrypted.handles[1],  // externalEuint64
  encrypted.handles[2],  // externalEuint8
  encrypted.inputProof   // single proof for all
);
```

---

## Decrypting Values for Display

Only authorized addresses (those with ACL permission) can decrypt values.

### User Decryption

```typescript
// Read the encrypted handle from the contract
const encryptedBalance = await contract.balanceOf(userAddress);

// Decrypt using the user's permission
const balance = await fhevm.decrypt(contractAddress, encryptedBalance);
// balance is now a BigInt you can display
```

### Handling Decryption States in UI

```typescript
// React example
function BalanceDisplay({ contractAddress, userAddress }) {
  const [balance, setBalance] = useState<bigint | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchBalance() {
      setLoading(true);
      try {
        const handle = await contract.balanceOf(userAddress);
        const decrypted = await fhevm.decrypt(contractAddress, handle);
        setBalance(decrypted);
      } catch (err) {
        // User may not have ACL permission
        setBalance(null);
      }
      setLoading(false);
    }
    fetchBalance();
  }, [userAddress]);

  if (loading) return <span>Decrypting...</span>;
  if (balance === null) return <span>Hidden</span>;
  return <span>{formatUnits(balance, 6)} CONF</span>;
}
```

**Key UX patterns:**
- Show "Decrypting..." while waiting for KMS response
- Show "Hidden" if the user doesn't have ACL permission
- Never show the raw handle — it's meaningless to users
- Cache decrypted values to avoid repeated KMS calls

---

## Transaction Flow

### Standard Encrypted Transfer UI

```
1. User enters amount (plaintext in the UI)
2. Click "Transfer" button
3. UI encrypts the amount client-side (fhevmjs)
4. UI submits transaction with encrypted handle + proof
5. Show "Transaction pending..." while tx confirms
6. After confirmation, re-fetch and decrypt updated balances
7. Show "Decrypting new balance..." during KMS request
8. Display updated balance
```

### Button States

Every encrypted transaction needs these states:

```typescript
// Button states for encrypted operations
type ButtonState =
  | "idle"           // Ready to click
  | "encrypting"     // Encrypting input client-side
  | "confirming"     // Waiting for wallet signature
  | "pending"        // Transaction submitted, waiting for confirmation
  | "decrypting"     // Fetching updated encrypted values
  | "complete";      // Done

// Show appropriate text for each state
function getButtonText(state: ButtonState): string {
  switch (state) {
    case "encrypting": return "Encrypting...";
    case "confirming": return "Confirm in wallet...";
    case "pending": return "Transaction pending...";
    case "decrypting": return "Updating balance...";
    case "complete": return "Done!";
    default: return "Transfer";
  }
}
```

---

## What Users Can and Cannot See

| Data | Visible to everyone | Visible to authorized user |
|------|--------------------|-----------------------------|
| Transaction sender/recipient | Yes | Yes |
| Function called | Yes | Yes |
| Encrypted input handles | Yes (but meaningless) | Yes (can decrypt) |
| Encrypted balances | No (handle only) | Yes (can decrypt own) |
| Transfer amounts | No | Sender and recipient only |
| Total supply (if plaintext) | Yes | Yes |
| Token name/symbol | Yes | Yes |

---

## Common Mistakes

### 1. Displaying Raw Handles

```typescript
// ❌ WRONG — shows something like "0x1a2b3c..." which means nothing
<span>Balance: {encryptedBalance.toString()}</span>

// ✅ CORRECT — decrypt first, then display
const decrypted = await fhevm.decrypt(contractAddr, encryptedBalance);
<span>Balance: {formatUnits(decrypted, 6)}</span>
```

### 2. No Loading State for Decryption

```typescript
// ❌ WRONG — shows 0 or undefined while decrypting
<span>Balance: {balance || 0}</span>

// ✅ CORRECT — explicit loading state
{isDecrypting ? <Spinner /> : <span>{formatBalance(balance)}</span>}
```

### 3. Assuming Instant Decryption

```typescript
// ❌ WRONG — decryption is async, not instant
const balance = fhevm.decrypt(addr, handle); // Missing await!

// ✅ CORRECT
const balance = await fhevm.decrypt(addr, handle);
```
