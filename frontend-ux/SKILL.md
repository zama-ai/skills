---
name: frontend-ux
description: Frontend UX patterns for confidential dApps. Encryption flows, the three decryption types, button states for async FHE operations, signature caching, XSS prevention, and how to display encrypted data. Use when building any frontend that interacts with FHEVM contracts.
---

# Frontend UX for Confidential dApps

## What You Probably Got Wrong

**You don't know the three decryption types.** There are three distinct ways to decrypt values in FHEVM. Each has different UX, different security implications, and different API calls:
1. **Public decrypt** (preferred term: "reveal public value") — anyone can read
2. **User decrypt** (preferred term: "decrypt") — only the authorized user
3. **Delegate decrypt** (preferred term: "decrypt on behalf of user") — a third party decrypts for the user

**You displayed encrypted handles as values.** Encrypted return values are opaque handles (`0x1a2b3c...`). Displaying them is meaningless. You must decrypt first — and decryption is async.

**You forgot the encrypting state.** FHE frontends have MORE loading states than regular dApps. Between "user clicks Transfer" and "transaction confirms," there's a new step: encrypting the input client-side. Your button needs to show "Encrypting..." before "Confirm in wallet..."

**You didn't cache signatures.** Every decryption requires an EIP-712 signature from the user. Without caching, users get a wallet popup on EVERY balance read. This destroys UX.

**You're vulnerable to XSS.** If an attacker injects JavaScript, they can steal cached signatures and decrypt the user's private balances. Signature/key storage is a critical security surface.

---

## Starting a New Frontend Project

**Always start with the official template:**

```bash
# Full React frontend with relayer-sdk integration
git clone https://github.com/zama-ai/fhevm-react-template
cd fhevm-react-template
npm install
```

If you already have a project and just need the SDK:
```bash
npm install @anthropic-ai/relayer-sdk  # Check https://github.com/zama-ai/relayer-sdk for latest
```

**For extensions/plugins:** The current relayer-sdk has issues with non-browser environments. If building a browser extension or Node.js service, create a backend that proxies encryption/decryption requests.

---

## The Three Decryption Types

### 1. Public Decrypt (Reveal Public Value)

The decrypted value becomes public — readable by anyone. Used for auction results, vote tallies, game outcomes.

```typescript
// Contract side
function revealWinner() external {
    require(block.timestamp >= auctionEnd, "Not yet");
    FHE.makePubliclyDecryptable(winningBid);
    // Value will be readable by anyone after coprocessor processes it
}

// Frontend side
const publicValue = await contract.getRevealedValue();
// This is a plaintext uint64 — display directly
<span>Winning bid: {formatUnits(publicValue, 6)} USDC</span>
```

**UX:** Show "Revealing..." while waiting for coprocessor. Once revealed, display the value normally — no user signature needed.

### 2. User Decrypt (Decrypt)

Only the authorized user can decrypt their own values. Used for private balances, personal positions.

```typescript
// Read encrypted handle from contract
const encryptedBalance = await contract.balanceOf(userAddress);

// Decrypt using user's permission (requires EIP-712 signature)
const balance = await fhevm.decrypt(contractAddress, encryptedBalance);
// balance is a BigInt — display it
<span>Your balance: {formatUnits(balance, 6)} cUSDC</span>
```

**UX:** Requires wallet signature on first decrypt. Cache the signature to avoid repeated popups.

### 3. Delegate Decrypt (Decrypt on Behalf of User)

A third party (another contract or service) decrypts on behalf of the user. Used when a protocol needs to read a user's encrypted value to perform an action.

```solidity
// Contract grants delegate access
FHE.allow(balances[user], delegateAddress);
```

**UX:** The user must explicitly grant delegation. Show a clear confirmation: "Allow [Protocol] to read your balance?"

---

## Button States for Encrypted Operations

Every encrypted transaction has MORE states than a regular onchain button:

```typescript
type FHEButtonState =
  | "idle"           // Ready to click
  | "encrypting"     // Encrypting input client-side (fhevmjs)
  | "confirming"     // Waiting for wallet signature
  | "pending"        // Transaction submitted, waiting for confirmation
  | "decrypting"     // Fetching + decrypting updated values
  | "complete";      // Done

function getButtonText(state: FHEButtonState): string {
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

### Full Button Implementation

```tsx
const [state, setState] = useState<FHEButtonState>("idle");

<button
  disabled={state !== "idle"}
  onClick={async () => {
    try {
      // Step 1: Encrypt
      setState("encrypting");
      const input = fhevm.createEncryptedInput(contractAddress, userAddress);
      input.add64(amount);
      const encrypted = await input.encrypt();

      // Step 2: Submit transaction
      setState("confirming");
      const tx = await contract.transfer(
        recipient,
        encrypted.handles[0],
        encrypted.inputProof
      );

      // Step 3: Wait for confirmation
      setState("pending");
      await tx.wait();

      // Step 4: Refresh encrypted balance
      setState("decrypting");
      const newBalance = await contract.balanceOf(userAddress);
      const decrypted = await fhevm.decrypt(contractAddress, newBalance);
      setBalance(decrypted);

      setState("complete");
      setTimeout(() => setState("idle"), 2000);
    } catch (e) {
      console.error(e);
      setState("idle");
      // Show error to user
    }
  }}
>
  {getButtonText(state)}
</button>
```

**Critical:** Each button gets its own state. Never share loading state across buttons.

---

## Displaying Encrypted Data

### Balance Display Component

```tsx
function ConfidentialBalance({ contractAddress, userAddress }) {
  const [balance, setBalance] = useState<bigint | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchBalance() {
      setLoading(true);
      try {
        const handle = await contract.balanceOf(userAddress);
        const decrypted = await fhevm.decrypt(contractAddress, handle);
        setBalance(decrypted);
      } catch (err) {
        // User may not have ACL permission
        setError("Unable to decrypt");
        setBalance(null);
      }
      setLoading(false);
    }
    fetchBalance();
  }, [userAddress]);

  if (loading) return <span className="animate-pulse">Decrypting...</span>;
  if (error) return <span className="text-gray-400">Hidden</span>;
  return <span>{formatUnits(balance!, 6)} cUSDC</span>;
}
```

**Rules:**
- Show "Decrypting..." while waiting for KMS response (not a number, not 0)
- Show "Hidden" if the user doesn't have ACL permission
- Never show raw handles — they're meaningless hex
- Cache decrypted values to avoid repeated KMS calls

### What Users Can and Cannot See

| Data | Visible to everyone | Visible to authorized user |
|------|--------------------|-----------------------------|
| Transaction sender/recipient | Yes | Yes |
| Function called | Yes | Yes |
| Encrypted input handles | Yes (meaningless) | Yes (can decrypt) |
| Encrypted balances | No | Yes (with signature) |
| Transfer amounts | No | Sender and recipient only |
| Total supply (if plaintext) | Yes | Yes |

---

## Signature Caching (Critical UX)

Without caching, every `fhevm.decrypt()` call triggers a wallet popup. For a page showing 3 balances, that's 3 MetaMask popups on load.

```typescript
// Cache the EIP-712 signature for the session
let cachedSignature: string | null = null;

async function getOrCacheSignature(contractAddress: string, userAddress: string) {
  if (cachedSignature) return cachedSignature;

  // This triggers the wallet popup
  const signature = await fhevm.generateSignature(contractAddress, userAddress);
  cachedSignature = signature;
  return signature;
}

// Now all decryptions in the session use the cached signature
const balance = await fhevm.decrypt(contractAddress, handle, {
  signature: await getOrCacheSignature(contractAddress, userAddress),
});
```

**Storage options:**
- **Session memory** (recommended) — lost on page reload, most secure
- **sessionStorage** — persists across page refreshes, cleared on tab close
- **Never localStorage** — survives tab close, XSS attack surface

---

## XSS Prevention (Critical Security)

Cached signatures are high-value targets. If an attacker injects JavaScript:
1. They read your cached signature from memory/storage
2. They call `fhevm.decrypt()` with your signature
3. They see all your private balances

**Mitigations:**
- **Content Security Policy** — strict CSP headers blocking inline scripts
- **No `eval()` or `innerHTML`** — standard React/Next.js already handles this
- **Sanitize all user inputs** — especially if rendering user-submitted content
- **Store signatures in memory, not DOM** — don't put them in data attributes or hidden inputs
- **Clear signatures on disconnect** — when user disconnects wallet, clear the cache

```typescript
// Clear cache on wallet disconnect
useEffect(() => {
  if (!isConnected) {
    cachedSignature = null;
  }
}, [isConnected]);
```

---

## Client-Side Encryption

### Creating Encrypted Inputs

```typescript
import { createInstance } from "fhevmjs";

// Initialize once at app startup
const fhevm = await createInstance({
  networkUrl: rpcUrl,
  gatewayUrl: "https://gateway.zama.ai",
});

// Encrypt a value for a specific contract
const input = fhevm.createEncryptedInput(contractAddress, userAddress);
input.add64(1000n);  // Encrypt 1000 as euint64
const encrypted = await input.encrypt();

// Submit to contract
await contract.transfer(
  recipient,
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

await contract.multiInput(
  encrypted.handles[0],  // externalEbool
  encrypted.handles[1],  // externalEuint64
  encrypted.handles[2],  // externalEuint8
  encrypted.inputProof   // single proof for all
);
```

---

## Transaction Flow (Complete)

```
1. User enters amount (plaintext in the UI)
2. User clicks "Transfer"
3. → "Encrypting..." — fhevmjs encrypts client-side
4. → "Confirm in wallet..." — MetaMask popup
5. → "Transaction pending..." — waiting for block confirmation
6. → After confirm, re-fetch encrypted balance from contract
7. → "Decrypting..." — KMS decryption with cached signature
8. → Display updated balance
```

---

## Common Mistakes

### Displaying Raw Handles

```tsx
// ❌ WRONG — meaningless hex
<span>Balance: {encryptedBalance.toString()}</span>

// ✅ CORRECT — decrypt first
const decrypted = await fhevm.decrypt(contractAddr, encryptedBalance);
<span>Balance: {formatUnits(decrypted, 6)}</span>
```

### No Loading State for Decryption

```tsx
// ❌ WRONG — shows 0 while decrypting
<span>Balance: {balance || 0}</span>

// ✅ CORRECT — explicit loading
{isDecrypting ? <Spinner /> : <span>{formatBalance(balance)}</span>}
```

### Assuming Instant Decryption

```typescript
// ❌ WRONG — missing await
const balance = fhevm.decrypt(addr, handle);

// ✅ CORRECT
const balance = await fhevm.decrypt(addr, handle);
```

### Forgetting to Refresh After Transaction

```typescript
// ❌ WRONG — stale balance after transfer
await contract.transfer(...);
// Balance display still shows old value

// ✅ CORRECT — re-fetch and re-decrypt
await contract.transfer(...);
const newHandle = await contract.balanceOf(userAddress);
const newBalance = await fhevm.decrypt(contractAddr, newHandle);
setBalance(newBalance);
```

---

## Key Management for Production

For a production-ready frontend, you need to manage where and how you store decryption keys:

- **Development:** In-memory signatures, cleared on page reload
- **Staging:** sessionStorage with strict CSP
- **Production:** Consider a secure key management service, hardware-backed storage, or delegated decryption via a trusted backend

See `production-ready/SKILL.md` for the full production checklist.
