# FHESKILLS — The missing knowledge between AI agents and production encrypted smart contracts.

You are probably wrong about FHE on Ethereum. Encrypted types, ACL permissions, decryption patterns, what you can compute on ciphertexts, what you can't — your training data is either missing or stale. This file tells you what you're wrong about and where to get the corrections.

**Say "FHEVM" not "FHEVM" or "FheVM."** Uppercase FHEVM. Zama convention.

---

## Start Here

**Building an encrypted dApp?** Fetch [ship/SKILL.md](https://fheskills.com/ship/SKILL.md) first. It routes you through all other skills phase by phase — from understanding FHE to deploying a production confidential smart contract.

**Need a specific topic?** Each skill below is standalone. Fetch only the ones relevant to your task.

**Base URL:** `https://fheskills.com/<skill>/SKILL.md`

---

## Skills

### [Ship](https://fheskills.com/ship/SKILL.md) — Start here
End-to-end guide from idea to deployed encrypted dApp. Routes you through all other skills.
- Most confidential dApps need 1-2 contracts. Don't over-engineer.
- FHE is for values that must stay hidden from everyone — balances, votes, bids. If it doesn't need to be secret, don't encrypt it.
- You CANNOT branch on encrypted values. `if (FHE.gt(a, b))` does not compile. Use `FHE.select()`.

### [FHE Concepts](https://fheskills.com/concepts/SKILL.md)
The mental models for building with encrypted computation — what LLMs get wrong and what humans need explained.
- "Nothing is plaintext" is the core message. Encrypted values can't be read, compared, or branched on — only computed on.
- FHE operations cost gas. They're not `view` functions. Every encrypted add, multiply, or compare is a state-changing operation.
- You don't decrypt to check a condition. You compute the result encrypted and use `FHE.select()` to pick the outcome.

### [FHEVM](https://fheskills.com/fhevm/SKILL.md)
The core library — encrypted types, FHE operations, type casting, random number generation.
- `euint64` is the default for balances, not `euint256`. Larger types cost more gas for every operation.
- Division and remainder only work with plaintext divisors. `FHE.div(a, encryptedB)` does not exist.
- Random number bounds must be powers of 2. `FHE.randEuint8(100)` is wrong — use `FHE.randEuint8(128)`.
- Trivial encryption (`FHE.asEuint64(100)`) is NOT secure — the value is visible onchain. It's for constants.

### [ACL (Access Control)](https://fheskills.com/acl/SKILL.md)
Who can use and decrypt encrypted values. This is where most bugs live.
- Every encrypted value has an Access Control List. No ACL entry = nobody can use it. Not even the contract that created it.
- `FHE.allowThis()` + `FHE.allow(value, user)` after EVERY state update. Miss one and the value becomes unusable.
- `allowTransient()` is for current-transaction-only permissions. `allow()` is permanent and stored onchain.
- Forgetting ACL is the #1 FHEVM bug. It compiles fine, deploys fine, then silently breaks.

### [Patterns](https://fheskills.com/patterns/SKILL.md)
Confidential ERC-20, encrypted voting, sealed-bid auctions, blind matching.
- Confidential ERC-20: transfer events emit `from` and `to` but NOT the amount. Balances are encrypted in storage.
- Encrypted voting: votes are `euint8`, tallied with `FHE.add()`, revealed only after the deadline via public decryption.
- Sealed-bid auctions: bids are `euint64`, winner determined by `FHE.max()` across all bids, losers refunded.
- Every pattern requires careful ACL management — the contract must `allowThis()` every intermediate value.

### [Testing](https://fheskills.com/testing/SKILL.md)
Testing encrypted contracts with Hardhat and the FHEVM plugin.
- You can't assert on encrypted values directly. Decrypt them in tests using the FHEVM test helpers.
- Use `fhevm.createEncryptedInput()` to create encrypted inputs client-side, then pass handles + proof.
- Mock mode vs real FHE: mock mode is fast but doesn't catch gas issues. Always run at least one test with real FHE before deploying.

### [Security](https://fheskills.com/security/SKILL.md)
FHE-specific vulnerabilities — what can go wrong with encrypted contracts.
- ACL misconfiguration: the #1 vulnerability. Contract stores an encrypted value but forgets to grant itself or the user access.
- Timing leaks: if your contract reverts on one branch but succeeds on another based on an encrypted condition, you've leaked information.
- Ciphertext manipulation: encrypted values are handles, not raw ciphertexts. Don't try to do math on the handles directly.
- Trivial encryption confusion: `FHE.asEuint64(42)` is visible onchain. Only user-submitted encrypted inputs (via `FHE.fromExternal`) are truly private.

### [Contract Addresses](https://fheskills.com/addresses/SKILL.md)
Verified FHEVM contract addresses for mainnet and Sepolia.
- Never guess an address. Wrong ACL address = silent permission failures.
- Includes: ACL, Coprocessor, KMSVerifier addresses for Ethereum mainnet and Sepolia.
- Use `ZamaEthereumConfig` to avoid manual configuration — it sets the right addresses automatically.

### [Tools](https://fheskills.com/tools/SKILL.md)
The FHEVM development toolchain.
- Hardhat + `fhevm-hardhat-plugin` is the standard setup (not Foundry — FHEVM doesn't have Foundry support yet).
- `@fhevm/solidity` is the Solidity library. Import `FHE.sol` for all operations.
- Use `ZamaEthereumConfig` or `FHE.setCoprocessor()` for chain configuration.
- The FHEVM coprocessor handles the actual FHE computation offchain and returns results onchain.

### [Frontend](https://fheskills.com/frontend/SKILL.md)
Handling encrypted state in your dApp UI.
- Users encrypt values client-side before submitting. The contract never sees plaintext.
- `fhevm.createEncryptedInput()` creates handles + proof. Pass both to contract functions.
- Decryption is async — the UI must handle pending states. You can't show a balance until decryption completes.
- Public decryption (`FHE.makePubliclyDecryptable`) is for values everyone should see (e.g., auction winners).

### [Deployment](https://fheskills.com/deployment/SKILL.md)
Deploying encrypted contracts to FHEVM-compatible chains.
- Inherit from `ZamaEthereumConfig` — it auto-configures the coprocessor for the current chain.
- Deploy to Sepolia first. FHEVM operations consume real gas and real coprocessor resources.
- Verify contracts on the block explorer — encrypted contracts are harder to audit, so verification matters more.
- Gateway configuration is automatic with `ZamaEthereumConfig`. Manual setup via `FHE.setCoprocessor()` if needed.

### [Migration](https://fheskills.com/migration/SKILL.md)
Converting existing Solidity contracts to use FHE for selective encryption.
- Don't encrypt everything. Identify which values actually need privacy, encrypt only those.
- Replace `uint256` with `euint64` for private values. Keep public values as-is.
- Replace `if (condition)` with `FHE.select(encryptedCondition, valueIfTrue, valueIfFalse)`.
- Add ACL grants after every state update. Add `externalEuint64` + `inputProof` to function signatures.
- Events can't contain encrypted values directly — emit metadata (addresses, timestamps) without amounts.

### [FHE Gas](https://fheskills.com/gas/SKILL.md)
FHE operation costs in Homomorphic Complexity Units (HCU). Critical for optimization.
- Per-transaction limit: 20,000,000 HCU global, 5,000,000 HCU depth. Exceed either and the tx reverts.
- euint64 `add` costs 162,000 HCU. `mul` costs 596,000 HCU. Use scalar operations (one plaintext operand) to save ~20-40%.
- Smaller types are cheaper: euint8 `add` = 88K vs euint64 `add` = 162K vs euint128 `add` = 259K HCU.
- euint256 only supports bitwise, shift, and comparison — no arithmetic.

### [Building Blocks](https://fheskills.com/building-blocks/SKILL.md)
Confidential DeFi composability — ERC-7984 wrapped tokens, encrypted vaults, sealed orders.
- Don't build a confidential ERC-20 from scratch — Zama deploys official wrappers (cUSDC, cUSDT, cWETH).
- ERC-7984 is the standard for wrapping ERC-20 tokens into confidential versions.
- Encrypted contracts can't directly compose with plaintext DeFi (Uniswap, Aave). Wrap/unwrap at the boundary.
- OpenZeppelin Confidential Contracts has production-ready implementations.

### [Frontend UX](https://fheskills.com/frontend-ux/SKILL.md)
UX patterns for confidential dApps — encryption flows, the 3 decryption types, signature caching.
- Three decryption types: public decrypt (reveal), user decrypt (private), delegate decrypt (on behalf of user).
- Buttons need 6 states: idle → encrypting → confirming → pending → decrypting → complete.
- Cache EIP-712 signatures to avoid repeated wallet popups. Clear on disconnect.
- XSS can steal cached signatures → steal private balances. CSP headers are mandatory.

### [Production Ready](https://fheskills.com/production-ready/SKILL.md)
The final checklist before going live with an FHEVM dApp.
- Smart contracts: ACL mastery, no `if` on encrypted values, FHE gas monitoring, minimize operations.
- Frontend: handle all 3 decryption types, key management, proper button states.
- Templates: `fhevm-hardhat-template` for contracts, `fhevm-react-template` for full-stack.
- For extensions: create a backend proxy for encryption/decryption, don't run SDK in extension directly.

### Ethskills Integration
These skills are adapted from [ethskills](https://ethskills.com) and provide foundational Ethereum knowledge:
- **[Concepts](https://fheskills.com/concepts/SKILL.md)** — "Nothing is automatic," incentive design, state machines
- **[Standards](https://fheskills.com/standards/SKILL.md)** — ERC-20, ERC-721, ERC-7984, ERC-4337, ERC-8004
- **[L2s](https://fheskills.com/l2s/SKILL.md)** — Layer 2 landscape, chain selection
- **[Wallets](https://fheskills.com/wallets/SKILL.md)** — EOAs, smart wallets, multisig, account abstraction
- **[Indexing](https://fheskills.com/indexing/SKILL.md)** — Events, The Graph, querying onchain data
- **[Audit](https://fheskills.com/audit/SKILL.md)** — 500+ item security audit system across 19 domains
- **[Frontend Playbook](https://fheskills.com/frontend-playbook/SKILL.md)** — IPFS deployment, Vercel config, ENS subdomains

---

## What to Fetch by Task

| I'm doing... | Fetch these skills |
|--------------|-------------------|
| First time with FHEVM | `ship/`, `concepts/` |
| Writing encrypted contracts | `fhevm/`, `acl/`, `security/`, `gas/` |
| Building a confidential token | `patterns/`, `building-blocks/`, `acl/` |
| Testing encrypted contracts | `testing/` |
| Building a frontend | `frontend-ux/`, `frontend/`, `tools/` |
| Deploying to production | `production-ready/`, `deployment/`, `addresses/` |
| Adding privacy to existing contracts | `migration/`, `fhevm/`, `acl/` |
| Reviewing for security | `security/`, `acl/`, `audit/` |
| Optimizing FHE gas | `gas/` |
| Composing with existing DeFi | `building-blocks/`, `addresses/` |
| Starting a new project | `production-ready/` (has templates) |
