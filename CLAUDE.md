# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**fheskills** is an external-facing skill set for AI agents building encrypted smart contracts with Zama's FHEVM (Fully Homomorphic Encryption Virtual Machine). It teaches developers how to build confidential dApps with smart contracts and frontends/backends that interact with the relayer-sdk.

**Deployed at:** https://fheskills.com (planned)
**Modeled after:** https://github.com/austintgriffith/ethskills
**License:** BSD-3-Clause-Clear (matches Zama licensing)

## Key Terminology

**Say "FHEVM" not "FHEVM" or "FheVM."** Lowercase "fh", uppercase "EVM". This is Zama's official convention.

## Developer Journey

### For Smart Contract Developers

If a developer is already good at writing smart contracts, they only need to learn **4 additional concepts**:

1. **Encrypted types** (`euint64`, `ebool`) and **FHE operations** (`FHE.add()`, `FHE.gt()`, `FHE.select()`)
2. **ACL (Access Control Lists)** - Who can use/decrypt encrypted values
3. **FHE limitations** - Cannot branch on encrypted values, division only with plaintext divisors
4. **No require/if pattern** - You bring all computation to the end using `FHE.select()` instead of reverting early

### For Frontend/Backend Developers

Developers building UIs or services that interact with encrypted contracts need to understand:

1. **Encryption** - How to encrypt values client-side before sending to contract
2. **Decryption** - Two types:
   - **Public decrypt** - Anyone can decrypt (e.g., auction winner)
   - **User decrypt** - Only specific user can decrypt (e.g., private balance)
3. **Signature caching** - Cache signatures to avoid repeated wallet prompts (critical UX pattern)
4. **XSS prevention** - Critical security pattern to prevent signature/key theft

All frontend/backend interaction happens via the **relayer-sdk**: https://github.com/zama-ai/relayer-sdk

## Starting Templates

**When a user wants to start a new project, ALWAYS offer these official templates:**

### Smart Contract Template
```bash
# FHEVM Hardhat Template - Complete Solidity development environment
git clone https://github.com/zama-ai/fhevm-hardhat-template
cd fhevm-hardhat-template
npm install
```
**Use for:** Writing and testing encrypted smart contracts

### Frontend Template
```bash
# FHEVM React Template - Frontend with relayer-sdk integration
git clone https://github.com/zama-ai/fhevm-react-template
cd fhevm-react-template
npm install
```
**Use for:** Building UIs that encrypt/decrypt and interact with encrypted contracts

## ERC-7984 and OpenZeppelin Confidential Contracts

**ERC-7984** is the standard for confidential wrapped tokens - wrapping existing ERC-20 tokens (like USDC, USDT, DAI) into their confidential encrypted versions.

**CRITICAL:** When building smart contracts, ALWAYS refer to **OpenZeppelin Confidential Contracts** for sample implementations and best practices:

**Repository:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts

This repo contains:
- **ERC-7984 implementation** - Confidential wrapped token standard
- **Sample contracts** - Production-ready examples for common patterns
- **Best practices** - Battle-tested patterns from OpenZeppelin

### When to Use ERC-7984

Use ERC-7984 when you need to:
- Wrap existing ERC-20 tokens (USDC, DAI, etc.) into confidential versions
- Enable private transfers while maintaining compatibility with public tokens
- Bridge between public and confidential token economies

### Example Pattern from OpenZeppelin

Instead of writing confidential contracts from scratch, check if OpenZeppelin has a sample for your use case:
- Confidential ERC-20 tokens
- Confidential voting systems
- Confidential auctions
- Wrapped token patterns

**Development workflow:**
1. Browse https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
2. Find the pattern closest to your use case
3. Adapt the OpenZeppelin sample to your needs
4. Maintain ACL patterns and security practices from their implementation

### Installation in Hardhat Project

To add OpenZeppelin Confidential Contracts to your Hardhat project:

```bash
npm install @openzeppelin/confidential-contracts
```

### Usage Pattern - Basic ERC7984 Example

**CRITICAL:** All contracts using confidentiality MUST inherit from `ZamaEthereumConfig` first, then `ERC7984`:

```solidity
// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.24;

import {Ownable2Step, Ownable} from "@openzeppelin/contracts/access/Ownable2Step.sol";
import {FHE, externalEuint64, euint64} from "@fhevm/solidity/lib/FHE.sol";
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaEthereumConfig.sol";
import {ERC7984} from "@openzeppelin/confidential-contracts/token/ERC7984/ERC7984.sol";

contract ERC7984Example is ZamaEthereumConfig, ERC7984, Ownable2Step {
    constructor(
        address owner,
        uint64 amount,
        string memory name_,
        string memory symbol_,
        string memory tokenURI_
    ) ERC7984(name_, symbol_, tokenURI_) Ownable(owner) {
        euint64 encryptedAmount = FHE.asEuint64(amount);
        _mint(owner, encryptedAmount);
    }
}
```

### Usage Pattern - ERC7984 with Mint/Burn

```solidity
import {ERC7984} from "@openzeppelin/confidential-contracts/token/ERC7984/ERC7984.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {FHE, externalEuint64} from "@fhevm/solidity/lib/FHE.sol";
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaEthereumConfig.sol";

contract ERC7984MintableBurnable is ZamaEthereumConfig, ERC7984, Ownable {
    constructor(
        address owner,
        string memory name,
        string memory symbol,
        string memory uri
    ) ERC7984(name, symbol, uri) Ownable(owner) {}

    function mint(address to, externalEuint64 amount, bytes memory inputProof)
        public onlyOwner {
        _mint(to, FHE.fromExternal(amount, inputProof));
    }

    function burn(address from, externalEuint64 amount, bytes memory inputProof)
        public onlyOwner {
        _burn(from, FHE.fromExternal(amount, inputProof));
    }
}
```

### Usage Pattern - ERC7984 Wrapped Token (ERC20 → ERC7984)

Wrapping an existing ERC20 token into a confidential ERC7984 token:

```solidity
import {ERC7984ERC20Wrapper} from "@openzeppelin/confidential-contracts/token/ERC7984/extensions/ERC7984ERC20Wrapper.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {FHE} from "@fhevm/solidity/lib/FHE.sol";

contract MyWrappedToken is ERC7984ERC20Wrapper {
    constructor(
        IERC20 underlyingToken,
        string memory name,
        string memory symbol,
        string memory uri
    ) ERC7984ERC20Wrapper(underlyingToken)
      ERC7984(name, symbol, uri) {}

    // Wrap ERC20 → ERC7984 (confidential)
    function wrap(address to, uint256 amount) public virtual {
        // Take ownership of ERC20 tokens
        SafeERC20.safeTransferFrom(underlying(), msg.sender, address(this), amount);
        // Mint confidential ERC7984 tokens
        _mint(to, FHE.asEuint64(uint64(amount)));
    }

    // Unwrap ERC7984 → ERC20 requires decryption (see OpenZeppelin docs)
}
```

**Key differences from regular ERC-20:**
- All balances and transfer amounts are **encrypted** (`euint64` ciphertext handles)
- No public `balanceOf()` - balances are private
- Transfer events emit addresses but NOT amounts (privacy-preserving)
- Cannot use `require()` to check encrypted balances - use `FHE.select()` instead

### Available OpenZeppelin Confidential Contracts

Check the repo for sample implementations:
- **ERC-7984** - Confidential wrapped token standard
- **Confidential ERC-20** - Private token transfers
- **Confidential voting** - Private governance
- **Confidential auctions** - Sealed-bid patterns

**Security Note:** These contracts are provided as-is, updated frequently, and not formally audited. Use them as reference implementations and adapt security practices to your needs.

## Commands

### Development

```bash
# Preview locally (serve static markdown files)
python3 -m http.server 8000

# Then visit http://localhost:8000
```

### Deployment

Static markdown files deployed via Vercel. No build step required.

```bash
# Vercel deployment happens automatically on push to main
# Manual deploy: vercel --prod
```

## Architecture

### Skill-Based Structure

Each skill is a standalone SKILL.md file in its own directory:

```
fheskills/
├── SKILL.md              # Router - links to all skills
├── ship/SKILL.md         # Entry point - routes through all phases
├── concepts/SKILL.md     # Mental models ("nothing is plaintext")
├── fhevm/SKILL.md        # Core API - euint types, FHE operations
├── acl/SKILL.md          # Access Control Lists (#1 bug source)
├── patterns/SKILL.md     # Confidential ERC-20, voting, auctions
├── testing/SKILL.md      # Hardhat + FHEVM plugin testing
├── security/SKILL.md     # FHE-specific vulnerabilities
├── addresses/SKILL.md    # Verified contract addresses
├── tools/SKILL.md        # Hardhat toolchain
├── frontend/SKILL.md     # Client-side encryption with fhevmjs
├── deployment/SKILL.md   # Deploying to FHEVM chains
└── migration/SKILL.md    # Adding FHE to existing contracts
```

**URL pattern:** `https://fheskills.com/<skill>/SKILL.md`

### Content Methodology

Inherited from ethskills' research-backed approach:

1. **Triage first** - Spawn a stock LLM, give it a realistic FHE task, document what it gets wrong
2. **Classify every line** - 🔴 (LLM blind spot), 🟣 (human teaching material), 🟡 (knows but skips), 🟢 (already knows + doesn't need teaching)
3. **Keep only 🔴 and 🟣** - Cut everything else

**The rule:** Every line must either fill a verified LLM blind spot OR teach essential concepts to humans. If stock LLMs already know it AND humans don't need it explained, cut it.

See ethskills' CONTRIBUTING.md for full methodology: https://github.com/austintgriffith/ethskills/blob/master/CONTRIBUTING.md

### File Conventions

- **SKILL.md** - Main content (each subdirectory has one)
- **CLAUDE.md** - This file (development guidance for Claude Code)
- **AGENTS.md** - Symlink to SKILL.md (for agent discovery)
- **llms.txt** - Symlink to SKILL.md (for LLM discoverability)
- **HANDOFF.md** - Project status snapshot (current state, what's done, what's missing)

## Critical Patterns

### ACL (Access Control Lists)

The #1 FHEVM bug is forgetting ACL grants. Every encrypted value needs permission grants:

```solidity
// WRONG - value is created but nobody can use it
euint64 balance = FHE.add(oldBalance, amount);

// CORRECT - grant permissions after every state update
euint64 balance = FHE.add(oldBalance, amount);
FHE.allowThis(balance);      // Contract can use it
FHE.allow(balance, user);    // User can use it
```

**Why this matters:** Missing ACL compiles fine, deploys fine, then silently fails at runtime. No revert, no error message - the value just becomes unusable.

### You Cannot Branch on Encrypted Values (Bring Computation to the End)

Since you cannot use `if` statements or `require` with encrypted values, you must **bring all computation to the end** using `FHE.select()`:

```solidity
// WRONG - this does not compile
if (FHE.gt(encryptedBalance, encryptedAmount)) {
    // transfer
}
require(FHE.gt(encryptedBalance, encryptedAmount), "Insufficient balance");

// CORRECT - use FHE.select() to compute both branches encrypted
euint64 amountToTransfer = FHE.select(
    FHE.gt(encryptedBalance, encryptedAmount),
    encryptedAmount,  // if true - sufficient balance
    FHE.asEuint64(0)  // if false - insufficient balance, transfer 0
);

// All computation happens, result selected at the end based on encrypted condition
```

This is a fundamental mindset shift: **instead of early returns/reverts, compute all possible outcomes and select the correct one encrypted.**

### Type Conventions

- **euint64** is the default for balances (not euint256) - cheaper gas for every FHE operation
- **Trivial encryption** (`FHE.asEuint64(42)`) is NOT secure - the value is visible onchain. Only for constants.
- **Real encryption** comes from user-submitted inputs via `FHE.fromExternal(inputHandle, inputProof)`

### Address Verification

Never guess contract addresses. Addresses in `addresses/SKILL.md` are sourced from:
- **Core infra (ACL, Coprocessor, KMSVerifier):** `ZamaConfig.sol` in `github.com/zama-ai/fhevm/library-solidity/config/`
- **Protocol addresses (tokens, wrappers, staking):** `github.com/zama-ai/protocol-apps/tree/main/docs/addresses`

Always cross-check against block explorers before using.

### Frontend Encryption/Decryption Pattern

**Critical:** Always cache signatures and implement XSS prevention to protect user keys.

```javascript
// ENCRYPTION - Create encrypted input client-side
const input = await createEncryptedInput(contractAddress, userAddress);
input.add64(42);
const { handles, inputProof } = input.encrypt();

// Pass to contract
await contract.transfer(handles[0], inputProof);

// DECRYPTION - Two types:

// 1. User decrypt (only this user can decrypt)
const decrypted = await decrypt64(encryptedValue);
console.log(decrypted); // 42n

// 2. Public decrypt (anyone can decrypt - e.g., auction winner)
await contract.makePubliclyDecryptable(encryptedValue);
// Wait for coprocessor to decrypt
const publicValue = await getPublicValue(encryptedValue);
```

**XSS Prevention:** Never expose private keys or signatures in frontend state that could be stolen via XSS. Use secure key management practices.

**Signature Caching:** Cache EIP-712 signatures to avoid repeated wallet prompts - improves UX dramatically.

## Development Workflow

### Adding a New Skill

1. Create directory: `mkdir new-skill/`
2. Write `new-skill/SKILL.md` following the template:
   - What LLMs get wrong (the corrections)
   - Verified code examples
   - Common pitfalls with ACL
3. Update root `SKILL.md` to link to the new skill
4. Update `.claude-plugin/plugin.json` skills array
5. Test locally: `python3 -m http.server 8000`

### Editing Existing Skills

1. **Verify against reality first** - Check official Zama docs at https://docs.zama.ai/protocol
2. **Cross-check API patterns** - Verify against latest `@fhevm/solidity` npm package
3. **Test with a stock LLM** - Does a fresh LLM actually get this wrong?
4. **Classify the change** - Is it 🔴 (blind spot) or 🟣 (teaching material)?
5. **Cut if 🟢** - Don't keep content that LLMs already know AND humans don't need explained

### Verifying FHE API Changes

```bash
# Check latest FHEVM Solidity package
npm view @fhevm/solidity version
npm view @fhevm/solidity

# Check official docs
open https://docs.zama.ai/protocol
```

## What's Currently Missing

Per `HANDOFF.md`, the following are not yet complete:

1. **No commits** - Files are staged but not committed
2. **No remote repo** - Needs GitHub repo creation
3. **Blind-spot triage not run** - Content seeded from internal skills, not validated against LLM failure modes
4. **No CONTRIBUTING.md** - Should document the triage methodology
5. **No audit skill** - Could benefit from FHE-specific audit checklist (like ethskills' `audit/SKILL.md`)
6. **Domain not set up** - Needs fheskills.com + Vercel deployment

## Smart Contract Development Best Practices

### Critical Security Patterns (from ethskills)

Even with FHE, you still need to follow standard Solidity security practices:

#### 1. Token Decimals Vary
**USDC has 6 decimals, not 18.** When wrapping ERC-20s into ERC-7984:

```solidity
// ❌ WRONG — assumes 18 decimals
uint256 oneToken = 1e18;

// ✅ CORRECT — check decimals
uint256 oneToken = 10 ** IERC20Metadata(token).decimals();
```

Common decimals: USDC/USDT = 6, WBTC = 8, DAI/WETH = 18

#### 2. Reentrancy Protection
Use Checks-Effects-Interactions (CEI) pattern + `ReentrancyGuard`:

```solidity
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

function withdraw() external nonReentrant {
    euint64 bal = balances[msg.sender];

    // 1. Checks
    // (Can't use require with encrypted values - compute all paths)

    // 2. Effects - update state FIRST
    balances[msg.sender] = FHE.asEuint64(0);

    // 3. Interactions - external calls LAST
    (bool success,) = msg.sender.call{value: decryptedAmount}("");
    require(success, "Transfer failed");
}
```

**Note:** With FHE, you can't `require(bal > 0)` on encrypted values. Use `FHE.select()` to compute all paths.

#### 3. SafeERC20
Always use SafeERC20 for token operations (USDT doesn't return bool):

```solidity
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
using SafeERC20 for IERC20;

token.safeTransfer(to, amount);
token.safeApprove(spender, amount);
```

#### 4. Access Control
Every privileged function needs explicit restrictions:

```solidity
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

function emergencyWithdraw() external onlyOwner {
    // Only owner can call
}
```

#### 5. Input Validation
Validate all inputs (even though you can't branch on encrypted values):

```solidity
function deposit(uint256 amount, address recipient) external {
    require(amount > 0, "Zero amount");
    require(recipient != address(0), "Zero address");
    // Then proceed
}
```

### Testing Encrypted Contracts

#### What to Test
- ✅ **Edge cases:** Zero amounts, max values, unauthorized callers
- ✅ **ACL correctness:** Contract and users can use encrypted values
- ✅ **Decryption:** Public and user decrypt work correctly
- ✅ **Access control:** Only authorized addresses can call privileged functions
- ❌ **Don't test:** OpenZeppelin internals, getters, trivial functions

#### Test with Hardhat
```javascript
import { expect } from "chai";
import { ethers } from "hardhat";
import { createEncryptedInput, decrypt64 } from "fhevm";

describe("ConfidentialToken", function () {
  it("transfers encrypted amounts", async function () {
    const [alice, bob] = await ethers.getSigners();

    // Create encrypted input
    const input = await createEncryptedInput(contractAddress, alice.address);
    input.add64(100);
    const { handles, inputProof } = input.encrypt();

    // Transfer
    await contract.connect(alice).transfer(bob.address, handles[0], inputProof);

    // Decrypt and verify
    const bobBalance = await contract.balanceOf(bob.address);
    const decrypted = await decrypt64(bobBalance);
    expect(decrypted).to.equal(100n);
  });
});
```

### Pre-Deploy Security Checklist

Before deploying any FHEVM contract:

- [ ] **ACL grants** — `FHE.allowThis()` and `FHE.allow()` after EVERY state update
- [ ] **Access control** — every admin function has `onlyOwner` or role-based restriction
- [ ] **No branching on encrypted** — using `FHE.select()` instead of `if`/`require`
- [ ] **Token decimals** — no hardcoded `1e18` for tokens with different decimals
- [ ] **SafeERC20** — using SafeERC20 for all ERC-20 operations
- [ ] **Input validation** — zero address, zero amount, bounds checks
- [ ] **Reentrancy protection** — CEI pattern + `nonReentrant` on functions with external calls
- [ ] **Events emitted** — every state change emits event (addresses only, not amounts)
- [ ] **Tests pass** — encryption, decryption, ACL, edge cases all tested
- [ ] **Contract verified** — verified on block explorer after deploy

## Technical Reference

### Hardhat Only (No Foundry)

FHEVM does not have Foundry support. All testing uses Hardhat + `fhevm-hardhat-plugin`.

```javascript
// hardhat.config.js
import { fhevm } from "fhevm-hardhat-plugin";

export default {
  solidity: "0.8.24",
  networks: {
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL,
      accounts: [process.env.PRIVATE_KEY],
    },
  },
};
```

### Common FHE Operations

```solidity
// Import
import { FHE } from "@fhevm/solidity";

// Addition (encrypted + encrypted)
euint64 sum = FHE.add(a, b);

// Comparison (returns ebool)
ebool isGreater = FHE.gt(a, b);

// Selection (encrypted ternary)
euint64 result = FHE.select(condition, valueIfTrue, valueIfFalse);

// Random number (bound must be power of 2)
euint8 random = FHE.randEuint8(128);  // NOT FHE.randEuint8(100)

// Division (only with plaintext divisor)
euint64 half = FHE.div(amount, 2);  // OK
// euint64 result = FHE.div(a, encryptedB);  // DOES NOT EXIST
```

### Gas Costs

FHE operations cost gas. They are NOT `view` functions:

- Every encrypted add, multiply, compare is a state-changing operation
- Larger types (euint256) cost more than smaller types (euint64)
- Use the smallest type that fits your value range

## Reference Projects

- **ethskills** (`/Users/aurora/Desktop/aurora/ai-skills/ethskills/`) - Same structure, Ethereum-focused
- **zama-marketplace** (`/Users/aurora/Desktop/aurora/ai-skills/zama-marketplace/`) - Internal plugin system (different use case)

Both are available locally for reference but are separate projects.
