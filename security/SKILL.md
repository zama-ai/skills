---
name: security
description: FHE-specific vulnerabilities and security patterns. What can go wrong with encrypted contracts that can't go wrong with regular Solidity.
---

# Security — FHE-Specific Vulnerabilities

## What You Probably Got Wrong

**You think regular Solidity security is enough.** FHEVM inherits all standard Solidity vulnerabilities (reentrancy, access control, etc.) AND adds a new class of bugs unique to encrypted computation. This skill covers the FHE-specific ones. Standard Solidity security still applies.

**You think encrypted means secure.** Encrypting values doesn't automatically make your contract secure. ACL misconfig, information leaks through control flow, and trivial encryption confusion are all FHEVM-specific attack vectors.

---

## FHE-Specific Vulnerabilities

### 1. ACL Misconfiguration (Critical — #1 Bug)

The contract stores an encrypted value but forgets to grant itself or the user permission.

```solidity
// ❌ VULNERABLE — contract can't use this value on the next call
balances[user] = FHE.add(balances[user], amount);
// Missing: FHE.allowThis(balances[user]);
// Missing: FHE.allow(balances[user], user);

// ✅ SAFE — always set permissions after state update
balances[user] = FHE.add(balances[user], amount);
FHE.allowThis(balances[user]);
FHE.allow(balances[user], user);
```

**Impact:** Values become permanently unusable. The contract appears to work during deployment but fails on subsequent calls.

**Detection:** Test every function that updates encrypted state. Verify that the next call can still read and operate on the updated values.

### 2. Information Leaks via Control Flow

If your contract reverts or behaves differently based on an encrypted condition, you've leaked information.

```solidity
// ❌ LEAKS — revert reveals that balance < amount
function transfer(address to, euint64 amount) public {
    ebool sufficient = FHE.ge(balances[msg.sender], amount);
    // Decrypting to use in require leaks the comparison result
    require(FHE.decrypt(sufficient), "Insufficient balance");
    // ...
}

// ✅ SAFE — silent no-op preserves privacy
function transfer(address to, euint64 amount) public {
    ebool canTransfer = FHE.le(amount, balances[msg.sender]);
    euint64 transferValue = FHE.select(canTransfer, amount, FHE.asEuint64(0));
    // Transfer either the amount or 0 — observer can't tell which
    _transfer(msg.sender, to, transferValue);
}
```

**Other leak vectors:**
- **Gas consumption differences:** If one branch does more FHE operations than another, gas cost reveals the path
- **Event emission:** Emitting events conditionally on encrypted values reveals the condition
- **Return values:** Returning different values based on encrypted state leaks information

### 3. Trivial Encryption Confusion

`FHE.asEuint64(100)` wraps a plaintext value. It's visible to everyone onchain. Treating it as a secret is a bug.

```solidity
// ❌ NOT PRIVATE — everyone can see the initial balance is 1000
function initialize() public {
    balances[msg.sender] = FHE.asEuint64(1000);
    // The value 1000 is in the bytecode/calldata — visible onchain
}

// ✅ PRIVATE — mint is a known public action, but subsequent encrypted
// operations on this value produce truly encrypted results
function mint(uint64 amount) public onlyOwner {
    // amount is public (it's a plaintext parameter), but that's intentional
    // for minting. After this, all operations on the balance are encrypted.
    balances[owner()] = FHE.add(balances[owner()], amount);
    FHE.allowThis(balances[owner()]);
    FHE.allow(balances[owner()], owner());
}
```

**The rule:** Only values submitted via `FHE.fromExternal(handle, proof)` are truly encrypted from the start. Trivially encrypted constants are fine for defaults and comparisons — just don't pretend they're secrets.

### 4. Uninitialized Encrypted Values

Operating on an encrypted value that was never set can produce unexpected results.

```solidity
// ❌ DANGEROUS — balance might not be initialized
function withdraw(euint64 amount) public {
    euint64 newBalance = FHE.sub(balances[msg.sender], amount);
    // If balances[msg.sender] is uninitialized, this is undefined behavior
}

// ✅ SAFE — check initialization first
function withdraw(euint64 amount) public {
    require(FHE.isInitialized(balances[msg.sender]), "No balance");
    euint64 newBalance = FHE.sub(balances[msg.sender], amount);
    // ...
}
```

### 5. Timing Attacks on Decryption

If decryption timing reveals information about the value, you've leaked data.

```solidity
// ❌ LEAKS — different actions after decryption reveal the result
function processResult(euint64 encResult) public {
    FHE.makePubliclyDecryptable(encResult);
    // If you then take different actions based on the decrypted value
    // before it's publicly known, the timing of your actions leaks info
}

// ✅ SAFE — make decryption the LAST step, take no conditional actions
function revealResult(euint64 encResult) public {
    require(block.timestamp >= deadline, "Not yet");
    FHE.makePubliclyDecryptable(encResult);
    // No further actions — let observers read the result themselves
}
```

### 6. Missing Input Validation

Failing to validate encrypted inputs with `FHE.fromExternal()` can allow invalid ciphertexts.

```solidity
// ❌ DANGEROUS — using external handle without validation
function process(externalEuint64 amount) public {
    // Directly using the handle without proof validation
    euint64 val = euint64.wrap(externalEuint64.unwrap(amount));
    // This bypasses input verification!
}

// ✅ SAFE — always validate with proof
function process(
    externalEuint64 amount,
    bytes calldata inputProof
) public {
    euint64 val = FHE.fromExternal(amount, inputProof);
    // Validated — proceed safely
}
```

### 7. Encrypted Value in Events

Emitting encrypted handles in events leaks mutation information — the handle changes when the value changes.

```solidity
// ❌ LEAKS — handle changes reveal when values change
event BalanceUpdated(address user, euint64 newBalance);

// ✅ SAFE — emit only metadata
event Transfer(address indexed from, address indexed to);
// No amount, no balance — just the fact that a transfer happened
```

---

## Standard Solidity Vulnerabilities That Still Apply

FHEVM contracts are still Solidity contracts. Every standard vulnerability applies. Encryption does NOT protect you from these.

### Reentrancy

External calls can re-enter your contract with stale state. Use Checks-Effects-Interactions + `nonReentrant`:

```solidity
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

// ❌ VULNERABLE — state updated after external call
function withdraw() external {
    uint256 bal = balances[msg.sender];
    (bool success,) = msg.sender.call{value: bal}("");
    require(success);
    balances[msg.sender] = 0; // Too late
}

// ✅ SAFE — CEI pattern + guard
function withdraw() external nonReentrant {
    uint256 bal = balances[msg.sender];
    require(bal > 0, "Nothing to withdraw");
    balances[msg.sender] = 0;  // Effect BEFORE interaction
    (bool success,) = msg.sender.call{value: bal}("");
    require(success, "Transfer failed");
}
```

**Note for FHE:** You can't `require(bal > 0)` on encrypted values. Use `FHE.select()` to compute all paths, but still update encrypted state BEFORE any external calls.

### Token Decimals Vary

**USDC has 6 decimals, not 18.** When wrapping ERC-20s into confidential versions:

```solidity
// ❌ WRONG — assumes 18 decimals
uint256 oneToken = 1e18;

// ✅ CORRECT — check decimals
uint256 oneToken = 10 ** IERC20Metadata(token).decimals();
```

Common decimals: USDC/USDT = 6, WBTC = 8, DAI/WETH = 18.

### SafeERC20

Some tokens (USDT) don't return `bool` on `transfer()`. Standard calls revert on success:

```solidity
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
using SafeERC20 for IERC20;

// ❌ WRONG — breaks with USDT
token.transfer(to, amount);

// ✅ CORRECT
token.safeTransfer(to, amount);
```

**Token quirks to watch for:**
- **Fee-on-transfer tokens:** Amount received < amount sent. Check balance before/after.
- **Rebasing tokens (stETH):** Balance changes without transfers. Use wrapped versions (wstETH).
- **Pausable/blocklist tokens (USDC, USDT):** Transfers can revert if paused or address is blocked.

### No Floating Point

Solidity has no `float`. Division truncates to zero:

```solidity
// ❌ WRONG — this equals 0
uint256 fivePercent = 5 / 100;

// ✅ CORRECT — basis points
uint256 FEE_BPS = 500; // 5% = 500 basis points
uint256 fee = (amount * FEE_BPS) / 10_000;
```

**Always multiply before dividing.** Division first = precision loss.

### Access Control

Every state-changing function needs explicit access control:

```solidity
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

// ❌ WRONG — anyone can drain
function emergencyWithdraw() external {
    token.transfer(msg.sender, token.balanceOf(address(this)));
}

// ✅ CORRECT
function emergencyWithdraw() external onlyOwner {
    token.transfer(owner(), token.balanceOf(address(this)));
}
```

### Input Validation

```solidity
function deposit(uint256 amount, address recipient) external {
    require(amount > 0, "Zero amount");
    require(recipient != address(0), "Zero address");
    require(amount <= maxDeposit, "Exceeds max");
}
```

### Front-Running & MEV

Encrypted values help here — attackers can't see amounts in the mempool. But function selectors are still visible (they know you're calling `transfer()`), and the existence of a transaction leaks intent.

For plaintext parameters (addresses, deadlines), standard MEV protections apply:
- Use **Flashbots Protect RPC** for private mempool
- Set tight slippage limits on any DEX interactions

### Oracle Safety

If your encrypted contract uses price feeds, the same oracle security applies:

```solidity
// ❌ DANGEROUS — DEX spot price manipulable via flash loan
function getPrice() internal view returns (uint256) {
    (uint112 r0, uint112 r1,) = pair.getReserves();
    return (r1 * 1e18) / r0;
}

// ✅ SAFE — Chainlink with staleness check
function getPrice() internal view returns (uint256) {
    (, int256 price,, uint256 updatedAt,) = feed.latestRoundData();
    require(block.timestamp - updatedAt < 3600, "Stale price");
    require(price > 0, "Invalid price");
    return uint256(price);
}
```

---

## Pre-Deploy Security Checklist

### FHE-Specific

- [ ] Every encrypted state update has `FHE.allowThis()` + `FHE.allow()`
- [ ] No `if/require/assert` branches on encrypted conditions (use `FHE.select()`)
- [ ] No encrypted values in event parameters
- [ ] All external encrypted inputs validated with `FHE.fromExternal(handle, proof)`
- [ ] `FHE.isInitialized()` checked before operations on potentially unset values
- [ ] No `view` modifier on functions with FHE operations
- [ ] Trivial encryptions (`FHE.asEuint64(x)`) not treated as secrets
- [ ] Gas consumption doesn't vary based on encrypted conditions (constant-gas paths)
- [ ] Decryption only happens at intended reveal points (not during computation)

### Standard Solidity

- [ ] Reentrancy protection (CEI + `nonReentrant`) on all functions with external calls
- [ ] Access control on all privileged functions (`onlyOwner`, `AccessControl`)
- [ ] Input validation (zero address, zero amount, bounds checks)
- [ ] SafeERC20 for all token operations
- [ ] Token decimal handling — no hardcoded `1e18`
- [ ] Multiply before divide in all math
- [ ] Events emitted for every state change (addresses only, NOT encrypted values)
- [ ] No hardcoded addresses (use `ZamaEthereumConfig` or constructor params)
- [ ] Oracle staleness + sanity checks if using price feeds
- [ ] Contract verified on block explorer after deployment
