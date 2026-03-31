---
name: building-blocks
description: Confidential DeFi building blocks — how encrypted contracts compose with existing protocols, confidential wrapper tokens (ERC-7984), and patterns for private DeFi. Use when building encrypted DeFi integrations, wrapping existing tokens, or composing confidential protocols.
---

# Confidential DeFi Building Blocks

## What You Probably Got Wrong

**You built a confidential ERC-20 from scratch.** Zama already deploys official confidential wrappers (cUSDC, cUSDT, cWETH, etc.) via ERC-7984. Check `addresses/SKILL.md` before writing your own.

**You tried to compose encrypted values with plaintext DeFi.** You can't pass an `euint64` to Uniswap — it expects `uint256`. Confidential DeFi operates in its own ecosystem. You compose within the confidential layer, and wrap/unwrap at the boundary.

**You forgot the wrap/unwrap boundary.** Every confidential DeFi system has a boundary where plaintext tokens become encrypted (wrap) and encrypted tokens become plaintext (unwrap). The wrap is simple. The unwrap requires decryption — and decryption is async.

**You ignored OpenZeppelin Confidential Contracts.** OpenZeppelin has production-ready implementations for confidential tokens, voting, and auctions. Start there, not from scratch: https://github.com/OpenZeppelin/openzeppelin-confidential-contracts

---

## ERC-7984: The Confidential Token Standard

ERC-7984 is the standard for confidential wrapped tokens. It wraps existing ERC-20 tokens into encrypted versions with private balances.

### How It Works

```
Public ERC-20 (USDC)  ──[wrap]──→  Confidential ERC-7984 (cUSDC)
                                          │
                                    All balances encrypted
                                    All transfers private
                                    ACL controls who decrypts
                                          │
Confidential ERC-7984 (cUSDC) ──[unwrap]──→  Public ERC-20 (USDC)
                                    (requires async decryption)
```

### Basic ERC-7984 Token

```solidity
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaConfig.sol";
import {ERC7984} from "@openzeppelin/confidential-contracts/token/ERC7984/ERC7984.sol";
import {Ownable2Step, Ownable} from "@openzeppelin/contracts/access/Ownable2Step.sol";
import {FHE, externalEuint64, euint64} from "@fhevm/solidity/lib/FHE.sol";

contract MyConfidentialToken is ZamaEthereumConfig, ERC7984, Ownable2Step {
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

### Wrapping ERC-20 → ERC-7984

```solidity
import {ERC7984ERC20Wrapper} from "@openzeppelin/confidential-contracts/token/ERC7984/extensions/ERC7984ERC20Wrapper.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {FHE} from "@fhevm/solidity/lib/FHE.sol";

contract ConfidentialUSDC is ERC7984ERC20Wrapper {
    constructor(IERC20 usdc)
        ERC7984ERC20Wrapper(usdc)
        ERC7984("Confidential USDC", "cUSDC", "") {}

    // Wrap: plaintext USDC → encrypted cUSDC
    function wrap(address to, uint256 amount) public virtual {
        SafeERC20.safeTransferFrom(underlying(), msg.sender, address(this), amount);
        _mint(to, FHE.asEuint64(uint64(amount)));
    }

    // Unwrap: encrypted cUSDC → plaintext USDC (requires decryption)
}
```

**Key difference from regular ERC-20:**
- All balances are `euint64` (encrypted)
- No public `balanceOf()` — balances are private
- Transfer events emit addresses but NOT amounts
- Cannot `require()` on balances — use `FHE.select()` for silent failure

---

## Official Confidential Wrappers (Already Deployed)

**Don't build these yourself.** Zama has deployed official wrappers:

### Ethereum Mainnet
| Token | Symbol | Address |
|-------|--------|---------|
| Confidential USDC | `cUSDC` | `0xe978F22157048E5DB8E5d07971376e86671672B2` |
| Confidential USDT | `cUSDT` | `0xAe0207C757Aa2B4019Ad96edD0092ddc63EF0c50` |
| Confidential WETH | `cWETH` | `0xda9396b82634Ea99243cE51258B6A5Ae512D4893` |
| Confidential ZAMA | `cZAMA` | `0x80CB147Fd86dC6dEe3Eee7e4Cee33d1397d98071` |

See `addresses/SKILL.md` for the full list including Sepolia testnet mock wrappers.

---

## Composability Patterns

### Pattern 1: Confidential Vault

A vault that accepts confidential tokens and earns yield — all balances encrypted:

```solidity
contract ConfidentialVault is ZamaEthereumConfig {
    IERC7984 public immutable cToken;
    mapping(address => euint64) private shares;
    euint64 private totalShares;

    function deposit(externalEuint64 amount, bytes calldata proof) external {
        euint64 amt = FHE.fromExternal(amount, proof);

        // Transfer cTokens from user to vault
        cToken.transferFrom(msg.sender, address(this), amt);

        // Mint shares (simplified — real vault needs share price calc)
        shares[msg.sender] = FHE.add(shares[msg.sender], amt);
        FHE.allowThis(shares[msg.sender]);
        FHE.allow(shares[msg.sender], msg.sender);

        totalShares = FHE.add(totalShares, amt);
        FHE.allowThis(totalShares);
    }
}
```

### Pattern 2: Confidential Swap (Sealed Order)

Users submit encrypted swap orders. Nobody sees the amounts until execution:

```solidity
struct SealedOrder {
    address trader;
    euint64 amountIn;
    euint64 minAmountOut;
    address tokenIn;
    address tokenOut;
}

function submitOrder(
    address tokenIn,
    address tokenOut,
    externalEuint64 amountIn,
    externalEuint64 minAmountOut,
    bytes calldata proof
) external {
    euint64 amt = FHE.fromExternal(amountIn, proof);
    euint64 minOut = FHE.fromExternal(minAmountOut, proof);

    // Store encrypted order — nobody can see the amounts
    orders[nextOrderId] = SealedOrder({
        trader: msg.sender,
        amountIn: amt,
        minAmountOut: minOut,
        tokenIn: tokenIn,
        tokenOut: tokenOut
    });

    FHE.allowThis(amt);
    FHE.allowThis(minOut);
    // Don't allow others — order amounts are private until execution
}
```

### Pattern 3: Confidential Lending

Loan amounts and collateral ratios stay encrypted:

```solidity
function borrow(
    externalEuint64 collateralAmount,
    externalEuint64 borrowAmount,
    bytes calldata proof
) external {
    euint64 collateral = FHE.fromExternal(collateralAmount, proof);
    euint64 borrow = FHE.fromExternal(borrowAmount, proof);

    // Check collateral ratio (encrypted comparison)
    // collateral * price >= borrow * ratio
    euint64 collateralValue = FHE.mul(collateral, oraclePrice);
    euint64 requiredCollateral = FHE.mul(borrow, COLLATERAL_RATIO);
    ebool sufficient = FHE.ge(collateralValue, requiredCollateral);

    // If insufficient, borrow 0 (silent failure — privacy preserving)
    euint64 actualBorrow = FHE.select(sufficient, borrow, FHE.asEuint64(0));

    // Update state...
    FHE.allowThis(actualBorrow);
    FHE.allow(actualBorrow, msg.sender);
}
```

---

## The Wrap/Unwrap Boundary

Every confidential DeFi system interfaces with the plaintext world at two points:

### Wrapping (Plaintext → Encrypted)

Simple — user sends plaintext tokens, contract encrypts them:

```solidity
function wrap(uint256 amount) external {
    // 1. Take plaintext tokens
    SafeERC20.safeTransferFrom(underlying, msg.sender, address(this), amount);
    // 2. Mint encrypted equivalent
    _mint(msg.sender, FHE.asEuint64(uint64(amount)));
}
```

### Unwrapping (Encrypted → Plaintext)

Complex — requires async decryption through the coprocessor:

```
1. User requests unwrap with encrypted amount
2. Contract requests decryption from coprocessor
3. Wait for coprocessor callback (async — not instant)
4. Callback receives plaintext amount
5. Contract transfers plaintext tokens to user
```

**This is the most error-prone part of confidential DeFi.** The async decryption means unwrapping is NOT atomic — it spans multiple transactions.

---

## Composing with Existing DeFi

You generally **cannot** directly compose encrypted contracts with existing plaintext DeFi protocols (Uniswap, Aave, etc.). The boundary looks like:

```
Confidential Layer          │  Plaintext Layer
                            │
cUSDC ──[unwrap]──→         │  ──→ USDC ──→ Uniswap swap
                            │
Uniswap output ──→          │  ──→ WETH ──[wrap]──→ cWETH
```

To compose:
1. **Unwrap** encrypted tokens to plaintext (async decryption)
2. **Interact** with plaintext DeFi (Uniswap, Aave, etc.)
3. **Wrap** the result back to encrypted

**This is intentional** — the whole point is that the confidential layer keeps balances private. Mixing with plaintext DeFi would leak information.

---

## OpenZeppelin Confidential Contracts

**Always check here first** before building from scratch:

**Repository:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts

Available implementations:
- **ERC-7984** — Confidential wrapped tokens
- **Confidential ERC-20** — Private token transfers
- **Confidential voting** — Private governance
- **Confidential auctions** — Sealed-bid patterns

```bash
npm install @openzeppelin/confidential-contracts
```

---

## Guardrails

- **ACL on every state update** — the #1 bug. See `acl/SKILL.md`
- **FHE operations cost gas** — more operations = more FHE gas. See `gas/SKILL.md`
- **Decryption is async** — unwrapping is not atomic. Handle the callback correctly
- **Trivial encryption is not private** — `FHE.asEuint64(100)` is visible onchain. Only `FHE.fromExternal()` is truly encrypted
- **Encrypted math wraps around** — euint64 overflow wraps modularly, doesn't revert
- **Use the smallest type** — euint8 is cheaper than euint64 for small values
