---
name: general
description: General FHEVM knowledge for planning, architecture, and understanding encrypted computation. Covers FHE concepts, project planning, architecture decisions, chain selection, the development lifecycle, toolchain overview, and production readiness. Fetch this to plan your development or answer questions about FHEVM.
---

# General -- Planning & Understanding FHEVM Development

## What You Probably Got Wrong

**You jump to code without a plan.** Before writing a single line of Solidity, you need to know: what goes onchain, what stays offchain, which chain, how many contracts, and who calls every function. Skip this and you'll rewrite everything.

**You over-engineer.** Most dApps need 1-2 contracts. A token launch is 1 contract. An NFT collection is 1 contract. A marketplace that uses existing DEX liquidity needs 0 contracts. Three contracts is the upper bound for an MVP. If you're writing more, you're building too much.

**You put too much onchain.** Solidity is for ownership, transfers, and commitments. It's not a database. It's not an API. It's not a backend. If it doesn't involve trustless value transfer or a permanent commitment, it doesn't belong in a smart contract.

**You think "encrypted" means "secure".** Missing ACL grants, trivial encryption treated as private, revert-based information leaks, gas-cost side channels -- encryption is a tool, not a guarantee. Security requires understanding how information leaks through every channel.

**You think FHE is like ZK proofs.** ZK proves you know something without revealing it -- one-time proof, no computation on the secret. FHE lets you compute on encrypted data -- ongoing operations without ever decrypting. They solve different problems.

**You think FHE operations are free like view functions.** Every FHE operation (add, multiply, compare) is a state-changing transaction that costs gas. The coprocessor does the heavy lifting offchain, but the onchain accounting still happens.

**"I'll decrypt, check the condition, then re-encrypt."** No. The entire point of FHE is that you NEVER decrypt during computation. If you decrypt to check a condition, you've leaked the value to the blockchain -- every node sees it. Decrypt only for final output, and only to authorized parties.

---

## FHE Concepts -- Mental Models

### Nothing Is Plaintext

**This is the most important concept in FHEVM. If you internalize nothing else, internalize this.**

An encrypted value in FHEVM is a handle -- an opaque reference to a ciphertext managed by the coprocessor. You cannot:

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
Encrypted value --[FHE.add]-->      Encrypted result
                --[FHE.gt]-->       Encrypted boolean
                --[FHE.select]-->   Encrypted choice
                --[FHE.allow]-->    Decryptable by specific address
                --[makePubliclyDecryptable]--> Decryptable by anyone
```

### The Branch Problem

This is where every LLM gets stuck on the first try:

```solidity
// REGULAR SOLIDITY -- you check a condition and branch
if (balance >= amount) {
    // do the transfer
} else {
    // revert or skip
}

// FHEVM -- YOU CANNOT DO THIS
// FHE.ge(balance, amount) returns an ebool -- an ENCRYPTED boolean
// You can't use an encrypted boolean in an if statement
// The EVM doesn't know if it's true or false -- that's the whole point
```

**The solution is `FHE.select()` -- the encrypted ternary operator:**

```solidity
ebool canTransfer = FHE.le(amount, balance);

// If canTransfer is true: transferValue = amount
// If canTransfer is false: transferValue = 0
// Nobody knows which one it is -- the computation happens encrypted
euint64 transferValue = FHE.select(canTransfer, amount, FHE.asEuint64(0));

// Both paths execute, but with either the real amount or zero
balance = FHE.sub(balance, transferValue);
recipientBalance = FHE.add(recipientBalance, transferValue);
```

**Both branches always execute.** That's what makes it private -- an observer can't tell which branch was "taken" because both always run. The `FHE.select()` just determines which value is used.

### Information Leaks

Even with encrypted values, you can accidentally leak information:

- **Revert-based leaks** -- if the contract reverts when balance < amount, the revert itself reveals that the condition was false. Use `FHE.select()` to silently handle both cases without reverting.
- **Gas consumption differences** -- if one code path does 3 FHE operations and another does 1, an observer can tell which path was taken by looking at gas usage. Equalize gas costs across branches.
- **Event emission** -- emitting an encrypted value's handle in an event leaks mutation information. The handle changes when the value changes, so observers can track when balances update. Emit only metadata (addresses, timestamps), not encrypted values.
- **Return values** -- returning an encrypted handle to an unauthorized caller is meaningless but returning plaintext values that differ based on encrypted state is a leak.

**The rule:** If your contract behaves differently (reverts, costs different gas, emits different events) based on an encrypted value, you've leaked information about that value.

### Trivial vs Real Encryption

Two ways to create encrypted values -- and they are NOT equivalent:

```solidity
// TRIVIAL ENCRYPTION -- the value 100 is visible onchain to everyone
// This is for constants, defaults, and initial values
euint64 trivial = FHE.asEuint64(100);

// REAL ENCRYPTION -- the value is encrypted client-side, invisible onchain
// This is for user secrets (balances, amounts, votes, bids)
euint64 real = FHE.fromExternal(externalHandle, inputProof);
```

**`FHE.asEuint64(100)` is NOT private.** Anyone can see it's 100. Use trivial encryption for:
- Default values (`FHE.asEuint64(0)`)
- Public constants in comparisons
- Initialization of encrypted accumulators

**`FHE.fromExternal()` is truly encrypted.** Users encrypt values client-side using the SDK, submit the handle + proof, and the contract validates with `FHE.fromExternal()`.

### The ACL Mental Model

Every encrypted value is born with an empty access list. **Nobody can use it until permissions are explicitly granted.**

Think of it like a safe deposit box:
- The coprocessor holds the box (ciphertext)
- `FHE.allow(value, address)` gives someone a key to the box
- `FHE.allowThis(value)` gives the contract itself a key
- `FHE.allowTransient(value, address)` gives a temporary key that expires after the transaction
- Without a key, the value exists but is completely unusable

```
Created --> Empty ACL (nobody can use it)
        --[FHE.allowThis()]-->             Contract can use it in future calls
        --[FHE.allow(val, user)]-->        User can decrypt it
        --[FHE.allowTransient(val, addr)]--> Address can use it THIS TX ONLY
```

**The #1 bug in FHEVM development:** storing an encrypted value without calling `FHE.allowThis()`. On the next transaction, the contract tries to use the stored value and fails -- it doesn't have permission to access its own data. It compiles fine, deploys fine, then silently breaks at runtime.

### FHE vs ZK Proofs

| | ZK Proofs | FHE |
|---|-----------|-----|
| **What it does** | Prove you know something without revealing it | Compute on encrypted data without decrypting |
| **Duration** | One-time proof | Ongoing computation on secrets |
| **Data** | Prover holds plaintext, verifier sees nothing | Nobody holds plaintext during computation |
| **Use case** | "I'm over 18" without revealing age | Private token transfers, sealed bids |
| **Analogy** | Showing your ID through frosted glass | Doing math inside a locked box |

Different tools for different problems. Don't confuse them.

### Teaching Your Human

**"Why can't I just encrypt everything?"**
Every encrypted operation costs gas -- `FHE.add` costs more than a regular addition because the coprocessor has to do the computation on ciphertexts. Encrypt only what needs to be private. Public values (token name, total supply, timestamps) should stay plaintext -- they're cheaper and other contracts can read them directly.

**"Why can't I use if/else?"**
The EVM doesn't know if an encrypted boolean is true or false -- that's the privacy guarantee. Instead, you use `FHE.select()`, which is like a ternary operator that works on encrypted conditions. Both branches always execute, so nobody can tell which path was "really" taken.

**"How is this different from ZK proofs?"**
ZK proofs say "I know a secret that satisfies this condition" without revealing the secret. It's a one-time proof. FHE says "here's encrypted data -- compute on it without ever seeing it." FHE enables ongoing computation on secrets. ZK proves things about secrets. Different tools for different jobs.

**"What about performance?"**
FHE operations are slower than plaintext operations -- that's the tradeoff for privacy. The FHEVM coprocessor handles the heavy math offchain, so you're not paying for raw FHE on the EVM. But encrypted operations still cost more gas than plaintext ones. Design your contracts to minimize the number of FHE operations -- encrypt only what matters.

**"Can the coprocessor see my data?"**
The coprocessor performs computation on ciphertexts. It needs the evaluation key (which lets it compute on encrypted data) but NOT the decryption key. Only the Key Management Service (KMS) holds decryption keys, and decryption only happens when explicitly requested with proper ACL authorization.

---

## Project Planning

### Step 1: Ask What the User Wants

**Before doing ANYTHING, ask the user:**

> "What kind of project do you want to build?"
> 1. **Smart contracts only** -- Solidity + tests + deployment (use `fhevm-hardhat-template`)
> 2. **Full-stack dApp** -- contracts + React frontend (use `fhevm-react-template`)
> 3. **Custom setup** -- contracts + their own frontend/backend (Hardhat template + `@zama-fhe/sdk`)
> 4. **Make an existing project confidential** -- add encryption to specific values

**Do not assume they want contracts-only.** Many developers want a frontend from the start.

### Step 2: Plan the Architecture

Do this BEFORE writing any code. Every hour spent here saves ten hours of rewrites.

#### The Onchain Litmus Test

**Put it onchain if it involves:**
- Trustless ownership -- who owns this token/NFT/position?
- Trustless exchange -- swapping, trading, lending, borrowing
- Composability -- other contracts need to call it
- Censorship resistance -- must work even if your team disappears
- Permanent commitments -- votes, attestations, proofs

**Keep it offchain if it involves:**
- User profiles, preferences, settings
- Search, filtering, sorting
- Images, videos, metadata (store on IPFS, reference onchain)
- Business logic that changes frequently
- Anything that doesn't involve value transfer or trust

**Judgment calls:**
- Reputation scores -> offchain compute, onchain commitments (hashes or attestations)
- Activity feeds -> offchain indexing of onchain events
- Price data -> offchain oracles writing onchain (Chainlink)
- Game state -> depends on stakes. Poker with real money? Onchain. Leaderboard? Offchain.

#### MVP Contract Count

| What you're building | Contracts | Pattern |
|---------------------|-----------|---------|
| Token launch | 1 | ERC-20 with custom logic |
| NFT collection | 1 | ERC-721 with mint/metadata |
| Simple marketplace | 0-1 | Use existing DEX; maybe a listing contract |
| Vault / yield | 1 | ERC-4626 vault |
| Lending protocol | 1-2 | Pool + oracle integration |
| DAO / governance | 1-3 | Governor + token + timelock |
| AI agent service | 0-1 | Maybe an ERC-8004 registration |
| Prediction market | 1-2 | Market + resolution oracle |

**If you need more than 3 contracts for an MVP, you're over-building.** Ship the simplest version that works, then iterate.

#### State Transition Audit

For EVERY function in your contract, fill in this worksheet:

```
Function: ____________
Who calls it? ____________
Why would they? ____________
What if nobody calls it? ____________
Does it need gas incentives? ____________
```

If "what if nobody calls it?" breaks your system, you have a design problem. Fix it before writing code.

#### Chain Selection

FHEVM is currently supported on **Ethereum mainnet and Sepolia**. Chain selection is constrained by coprocessor availability.

| Chain | Status | Use for |
|-------|--------|---------|
| **Ethereum mainnet** | Supported | Production deployments |
| **Sepolia testnet** | Supported | Testing, staging |
| **L2s** | Not yet supported | Future expansion |

Use `ZamaEthereumConfig` in your contracts -- it auto-configures the correct coprocessor addresses for the current chain.

### dApp Archetype Templates

Find your archetype below. Each tells you exactly how many contracts you need, what they do, common mistakes, and which skills to fetch.

#### 1. Token Launch (1-2 contracts)

**Architecture:** One confidential ERC-20 contract. Add a vesting contract if you have team/investor allocations.

**Contracts:**
- `MyToken.sol` -- Confidential ERC-20 (ERC-7984) with encrypted balances
- `TokenVesting.sol` (optional) -- time-locked releases

**Common mistakes:**
- Infinite supply with no burn mechanism
- No initial liquidity plan
- Fee-on-transfer mechanics that break DEX integrations
- Forgetting `FHE.allowThis()` on balance updates

**Fetch sequence:** `solidity/SKILL.md` -> `addresses/SKILL.md`

#### 2. NFT Collection (1 contract)

**Architecture:** One ERC-721 contract. Metadata on IPFS. Frontend for minting.

**Contracts:**
- `MyNFT.sol` -- ERC-721 with mint, max supply, metadata URI

**Common mistakes:**
- Storing images onchain (use IPFS or Arweave)
- No max supply cap
- Complex whitelist logic when a simple Merkle root works

**Fetch sequence:** `solidity/SKILL.md` -> `typescript/SKILL.md`

#### 3. Marketplace / Exchange (0-2 contracts)

**Architecture:** If trading existing tokens, you likely need 0 contracts -- integrate with existing DEX liquidity. If building custom order matching with encrypted bids, 1-2 contracts.

**Contracts:**
- (often none -- use existing liquidity)
- `SealedOrderBook.sol` (if custom) -- encrypted bids, FHE.max() for matching
- `Escrow.sol` (if needed) -- holds assets during trades

**Common mistakes:**
- Building a DEX from scratch when existing infrastructure works
- Ignoring MEV protection
- Centralized order matching (defeats the purpose)

**Fetch sequence:** `solidity/SKILL.md` -> `addresses/SKILL.md`

#### 4. Lending / Vault / Yield (0-1 contracts)

**Architecture:** If using existing protocol, 0 contracts. If building a confidential vault, 1 contract with encrypted positions.

**Contracts:**
- `ConfidentialVault.sol` -- vault with encrypted deposit amounts

**Common mistakes:**
- Ignoring vault inflation attack
- Not using ERC-4626 standard (breaks composability)
- Hardcoding token decimals (USDC is 6, not 18)

**Fetch sequence:** `solidity/SKILL.md` -> `addresses/SKILL.md`

#### 5. DAO / Governance (1-3 contracts)

**Architecture:** Governor contract + governance token + timelock. Use OpenZeppelin's Governor with encrypted voting via FHE.

**Contracts:**
- `GovernanceToken.sol` -- ERC-20Votes or confidential token
- `ConfidentialGovernor.sol` -- encrypted vote tallying with FHE.add()
- `TimelockController.sol` -- delays execution for safety

**Common mistakes:**
- No timelock (governance decisions execute instantly = rug vector)
- Low quorum that allows minority takeover
- Not encrypting vote choices (defeats private voting)

**Fetch sequence:** `solidity/SKILL.md` -> `typescript/SKILL.md`

#### 6. AI Agent Service (0-1 contracts)

**Architecture:** Agent logic is offchain. Onchain component is optional -- ERC-8004 identity registration, or a payment contract.

**Contracts:**
- (often none -- agent runs offchain)
- `AgentRegistry.sol` (optional) -- identity + service endpoints

**Common mistakes:**
- Putting agent logic onchain (Solidity is not for AI inference)
- Overcomplicating payments
- Ignoring key management

**Fetch sequence:** `solidity/SKILL.md`

---

## The Development Lifecycle

### Step 3: Build Contracts

**Fetch:** `solidity/SKILL.md`

Key guidance:
- Use OpenZeppelin Confidential Contracts as your base -- don't reinvent encrypted ERC-20s
- Use verified addresses from `addresses/SKILL.md` -- never fabricate addresses
- Every contract inherits `ZamaEthereumConfig` first
- Follow CEI pattern (Checks-Effects-Interactions)
- `FHE.allowThis()` + `FHE.allow()` after EVERY encrypted state update
- No `if`/`require` on encrypted values -- only `FHE.select()`
- Emit events for every state change (addresses only, not encrypted values)

Use the template chosen in Step 1. The `solidity/SKILL.md` skill has complete Solidity patterns, ACL guides, gas optimization, and security checklists.

### Step 4: Test

**Fetch:** `solidity/SKILL.md` (testing section)

Don't skip this. Don't "test later." Test before deploy.

Key guidance:
- Unit test every custom function (not OpenZeppelin internals)
- Fuzz test all math operations
- Test ACL: call every function twice -- the second call proves ACL works
- Test edge cases: zero amounts, max values, unauthorized callers
- Run with `npx hardhat test` (plugin provides mock FHE environment)

**Security review:** After testing, give your contracts to a **separate agent in a fresh context** with the audit skill. A reviewer that didn't write the code catches bugs the author is blind to.

### Step 5: Build Frontend

**Skip this step if the user chose "smart contracts only" in Step 1.**

**Fetch:** `typescript/SKILL.md`

Key guidance:
- If using `fhevm-react-template`, the basic setup is already done
- If using a custom frontend, install `@zama-fhe/sdk`
- Implement the 6-state button flow: idle -> encrypting -> confirming -> pending -> decrypting -> complete
- Handle all 3 decryption types:
  - **Public decrypt** -- value revealed to everyone (auction results, vote tallies)
  - **User decrypt** -- only the authorized user can read (private balances)
  - **Delegate decrypt** -- a third party decrypts for the user (cross-contract reads)
- Cache EIP-712 signatures to avoid repeated wallet popups
- Show "Decrypting..." states -- FHE decryption is async, not instant
- Implement XSS prevention for cached signatures (use sessionStorage, not localStorage)

The `typescript/SKILL.md` skill has complete React/TypeScript patterns, SDK usage, and frontend security.

### Step 6: Ship to Production

Key guidance:

**Deploy Sepolia first.** Test the full flow -- encrypt, transact, decrypt -- on testnet before touching mainnet.

**Verify contracts** on the block explorer. Encrypted contracts are harder to audit, so verification matters more.

**Transfer ownership to a multisig** (Gnosis Safe). Never leave a single EOA as owner in production.

**Post-launch monitoring:**
- Monitor contract activity on block explorer
- Set up event monitoring with The Graph or Dune
- Have an incident response plan (pause mechanism if applicable)

---

## The FHEVM Toolchain

### The Stack

```
+---------------------------------------------------+
|  Your Contract (Solidity)                         |
|  imports @fhevm/solidity/lib/FHE.sol              |
+---------------------------------------------------+
|  Hardhat + @fhevm/hardhat-plugin                  |
|  Local FHE mock for testing                       |
+---------------------------------------------------+
|  FHEVM Host Contracts (onchain)                   |
|  ACL, FHEVMExecutor, KMSVerifier                  |
+---------------------------------------------------+
|  Coprocessor (offchain)                           |
|  Rust FHE computation engine                      |
+---------------------------------------------------+
|  KMS (Key Management Service)                     |
|  Holds decryption keys, handles key requests      |
+---------------------------------------------------+
```

### Key Packages

| Package | Purpose |
|---------|---------|
| `@fhevm/solidity` | Solidity library -- `FHE.sol`, encrypted types, configs |
| `@fhevm/hardhat-plugin` | Hardhat plugin -- local FHE mock for testing |
| `@zama-fhe/sdk` | Frontend SDK -- encrypt/decrypt client-side |
| `@zama-fhe/react-sdk` | React hooks -- React-specific bindings for the SDK |
| `@openzeppelin/confidential-contracts` | Production patterns -- ERC-7984, confidential tokens |

### Starting Templates

**Smart contracts only:**
```bash
git clone https://github.com/zama-ai/fhevm-hardhat-template <project-name>
cd <project-name>
npm install
```

**Full-stack dApp (contracts + React):**
```bash
git clone https://github.com/zama-ai/fhevm-react-template <project-name>
cd <project-name>
npm install
```

**Custom setup (your own frontend/backend):**
Start with the Hardhat template for contracts, then add the SDK:
```bash
npm install @zama-fhe/sdk
```

**Browser extensions:** The SDK has issues with non-browser environments. Create a backend proxy:
```
Extension --> Backend API --> @zama-fhe/sdk --> FHEVM
```

### Development Workflow

```
1. Write contract  --> import FHE.sol, inherit ZamaEthereumConfig
2. Write tests     --> use fhevm.createEncryptedInput() and fhevm.decrypt*()
3. Run tests       --> npx hardhat test (plugin provides mock FHE)
4. Deploy Sepolia  --> npx hardhat run scripts/deploy.ts --network sepolia
5. Verify          --> npx hardhat verify --network sepolia <address>
6. Deploy mainnet  --> same config, ZamaEthereumConfig handles chain detection
```

---

## Production Readiness Overview

### Smart Contract Requirements

1. **Already good at Solidity** -- FHEVM adds encrypted types on top of Solidity fundamentals. No unbounded loops, minimal storage writes, CEI pattern. If you're not confident in Solidity, fix that first.

2. **ACL mastery** -- `FHE.allowThis()` + `FHE.allow(value, user)` after EVERY state update. The #1 cause of production failures is missing ACL grants. Test by calling every function twice -- the second call proves ACL works.

3. **No `if` on encrypted values** -- only `FHE.select()`. Compute both paths, select the result encrypted. The contract always executes the same code path regardless of encrypted values.

4. **Minimize FHE operations** -- use scalar operations when one operand is plaintext (cheaper), use the smallest encrypted type that fits (euint8 add = 88K HCU vs euint64 add = 162K HCU), batch where possible.

5. **Monitor HCU limits** -- per-transaction: 20,000,000 HCU global, 5,000,000 HCU depth. If a function uses more than 10,000,000 HCU (50% of limit), split into multiple transactions.

For complete Solidity patterns, ACL guides, gas tables, and security checklists, fetch `solidity/SKILL.md`.

### Frontend Requirements

1. **Three decryption types** -- public (anyone reads), user (authorized user only), delegate (third party reads for user). Your frontend must handle all three correctly.

2. **Key management** -- cache EIP-712 signatures in sessionStorage (not localStorage -- XSS risk). Clear on wallet disconnect. Implement CSP headers.

3. **Button states** -- `idle -> encrypting -> confirming -> pending -> decrypting -> complete`. Every button needs its own loading state.

4. **Error handling** -- "Transaction reverted" with no reason = likely HCU limit exceeded. Decryption timeout = KMS may be slow, show retry. "Cannot decrypt" = no ACL permission, show "Hidden".

For complete TypeScript/React patterns and SDK usage, fetch `typescript/SKILL.md`.

### Deployment Requirements

1. **Sepolia first** -- test the full encrypt/transact/decrypt flow on testnet
2. **Verify contracts** -- on block explorer after deploy
3. **Transfer ownership to multisig** -- never leave a single EOA as owner
4. **Test one real transaction** -- mint, transfer, decrypt on testnet before mainnet

---

## Anti-Patterns

**Kitchen sink contract.** One contract doing everything -- swap, lend, stake, govern. Split responsibilities. Each contract should do one thing well.

**Factory nobody asked for.** Building a factory contract that deploys new contracts when you only need one instance. Factories are for protocols that serve many users creating their own instances. Most dApps don't need them.

**Onchain everything.** Storing user profiles, activity logs, images, or computed analytics in a smart contract. Use onchain for ownership and value transfer, offchain for everything else.

**Admin crutch.** Relying on an admin account to call maintenance functions. What happens when the admin loses their key? Design permissionless alternatives with proper incentives.

**Premature multi-chain.** Deploying to 5 chains on day one. Launch on one chain, prove product-market fit, then expand. Multi-chain adds complexity in bridging, state sync, and liquidity fragmentation.

**Reinventing audited primitives.** Writing your own confidential ERC-20, your own access control, your own math library. Use OpenZeppelin Confidential Contracts. They're battle-tested. Your custom version has bugs.

**Ignoring the frontend.** A working contract with a broken UI is useless. Most users interact through the frontend, not Etherscan. Budget 40% of your time for frontend polish.

---

## Skill Routing Table

| Phase | What you're doing | Skill to fetch |
|-------|-------------------|----------------|
| **Plan** | Architecture, concepts, project planning | `general/` (this skill) |
| **Contracts** | Writing encrypted Solidity, ACL, testing, security | `solidity/SKILL.md` |
| **Frontend** | Building UI with SDK, encryption/decryption flows | `typescript/SKILL.md` |
| **Addresses** | Contract addresses for mainnet and Sepolia | `addresses/SKILL.md` |

**Base URL:** `https://fheskills.com/<skill>/SKILL.md`

---

## Resources

- **Zama Documentation:** https://docs.zama.ai/protocol
- **FHEVM GitHub:** https://github.com/zama-ai/fhevm
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
- **ethskills (Ethereum development skills):** https://github.com/austintgriffith/ethskills
