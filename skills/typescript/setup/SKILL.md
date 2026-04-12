---
name: setup-typescript
description: "Set up a TypeScript frontend or backend for FHEVM. Use when users need to: (1) start a new React dApp with fhevm-react-template, (2) add @zama-fhe/sdk to an existing project, (3) set up encryption/decryption flows, or (4) configure a backend proxy for non-browser environments."
license: BSD-3-Clause-Clear
metadata:
  author: Zama
---

# FHEVM TypeScript Setup

Two paths depending on what you're building. Ask the developer: new React dApp or adding FHE to an existing project?

---

## Path 1: New React dApp (fhevm-react-template)

Clone the official template — it comes with the SDK, React hooks, wallet connection, and encryption/decryption flows pre-configured.

```bash
git clone https://github.com/zama-ai/fhevm-react-template
cd fhevm-react-template
npm install
npm run dev
```

The template includes:
- `@zama-fhe/sdk` and `@zama-fhe/react-sdk` pre-configured
- Wallet connection (wagmi/viem)
- Example encryption and decryption flows
- Signature caching setup

---

## Path 2: Add SDK to an Existing Project

```bash
npm install @zama-fhe/sdk
```

For React projects, also install the hooks:

```bash
npm install @zama-fhe/react-sdk
```

### Package Name History

The SDK was renamed twice. If you see old imports, update them:

| Old name | Current name |
|----------|-------------|
| `fhevmjs` | `@zama-fhe/sdk` |
| `@fhevm/sdk` | `@zama-fhe/sdk` |

Always use `@zama-fhe/sdk` for new projects.

### Key Packages

| Package | Purpose |
|---------|---------|
| `@zama-fhe/sdk` | Core SDK — encryption, decryption, signature generation |
| `@zama-fhe/react-sdk` | React hooks — `useFhevm()`, `useDecrypt()`, etc. |
| `@zama-fhe/relayer-sdk` | Relayer client for mainnet API key authentication |

---

## Non-Browser Environments

The SDK requires browser APIs (WebAssembly, crypto). For browser extensions, Node.js services, or server-side rendering, use a backend proxy:

```
Extension/Plugin → Your Backend API → @zama-fhe/sdk → FHEVM
```

The backend handles encryption/decryption. The frontend sends plaintext to your backend over HTTPS, and the backend encrypts before submitting to the contract.

---

## Mainnet: Relayer API Key

For mainnet, you need a Relayer API key. Install the relayer SDK:

```bash
npm install @zama-fhe/relayer-sdk
```

Configure with your API key:

```typescript
auth: { __type: 'ApiKeyHeader', value: process.env.ZAMA_FHEVM_API_KEY }
```

**Never embed the API key in frontend code.** Use a backend proxy that injects the `x-api-key` header.

Apply for a key: https://docs.zama.org/protocol/relayer-sdk-guides/fhevm-relayer/mainnet-api-key

Sepolia testnet does not require an API key.

---

## First Encryption

Regardless of setup path, your first encrypted input should look like this:

```typescript
import { createEncryptedInput } from '@zama-fhe/sdk';

// 1. Create encrypted input bound to contract + user
const input = await createEncryptedInput(contractAddress, userAddress);

// 2. Add the value to encrypt (64-bit unsigned integer)
input.add64(1000000n); // e.g., 1 USDC (6 decimals)

// 3. Encrypt — produces handles + ZKPoK proof
const { handles, inputProof } = await input.encrypt();

// 4. Pass to contract
await contract.transfer(recipientAddress, handles[0], inputProof);
```

**Key points:**
- Encryption happens client-side — the plaintext never hits the blockchain
- `handles[0]` is the encrypted reference the contract uses
- `inputProof` is the ZKPoK proving the encryption is valid
- A single `inputProof` covers all values added to the same `input`

---

## References

- [fhevm-react-template](https://github.com/zama-ai/fhevm-react-template) — React starter template
- [@zama-fhe/sdk](https://www.npmjs.com/package/@zama-fhe/sdk) — Core SDK
- [@zama-fhe/react-sdk](https://www.npmjs.com/package/@zama-fhe/react-sdk) — React hooks
- [Relayer API key](https://docs.zama.org/protocol/relayer-sdk-guides/fhevm-relayer/mainnet-api-key) — Mainnet access

For decryption patterns, button states, signature caching, and security, see the main [typescript/SKILL.md](../SKILL.md).
