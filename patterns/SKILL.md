---
name: patterns
description: Confidential ERC-20, encrypted voting, sealed-bid auctions, blind matching — the building block patterns for FHEVM dApps. Complete implementations with ACL, not just pseudocode.
---

# Patterns — Encrypted dApp Building Blocks

## What You Probably Got Wrong

**You emitted transfer amounts in events.** Confidential ERC-20 events emit `from` and `to` but NOT the amount. If you emit the amount, you've defeated the entire purpose of encrypting balances.

**You forgot ACL in your pattern.** Every pattern below requires ACL management after every encrypted state update. If a pattern doesn't show `FHE.allowThis()` and `FHE.allow()`, it's incomplete.

**You tried to implement standard ERC-20 with encrypted internals.** `balanceOf()` can't return a `uint256` if the balance is encrypted. The interface changes — `balanceOf()` returns `euint64`, and only authorized addresses can decrypt it.

---

## 1. Confidential ERC-20

The most common FHEVM pattern. Encrypted balances, encrypted transfer amounts, public metadata.

```solidity
// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.24;

import "@fhevm/solidity/lib/FHE.sol";
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaConfig.sol";
import "@openzeppelin/contracts/access/Ownable2Step.sol";

contract ConfidentialERC20 is Ownable2Step, ZamaEthereumConfig {
    mapping(address => euint64) internal balances;
    mapping(address => mapping(address => euint64)) internal allowances;

    uint64 private _totalSupply;  // Public — total supply is not secret
    string private _name;
    string private _symbol;
    uint8 public constant decimals = 6;

    // Events: addresses are public, amounts are NOT
    event Transfer(address indexed from, address indexed to);
    event Approval(address indexed owner, address indexed spender);

    constructor(string memory name_, string memory symbol_) Ownable(msg.sender) {
        _name = name_;
        _symbol = symbol_;
    }

    // Mint — plaintext amount, encrypted storage
    function mint(uint64 amount) public onlyOwner {
        balances[owner()] = FHE.add(balances[owner()], amount);
        FHE.allowThis(balances[owner()]);
        FHE.allow(balances[owner()], owner());
        _totalSupply += amount;
    }

    // Transfer — encrypted amount from user input
    function transfer(
        address to,
        externalEuint64 encryptedAmount,
        bytes calldata inputProof
    ) public returns (bool) {
        euint64 amount = FHE.fromExternal(encryptedAmount, inputProof);
        require(FHE.isSenderAllowed(amount), "Not allowed");

        ebool canTransfer = FHE.le(amount, balances[msg.sender]);
        _transfer(msg.sender, to, amount, canTransfer);
        return true;
    }

    function _transfer(
        address from,
        address to,
        euint64 amount,
        ebool canTransfer
    ) internal {
        // If canTransfer is false, transferValue becomes 0 — silent no-op
        euint64 transferValue = FHE.select(canTransfer, amount, FHE.asEuint64(0));

        // Update recipient
        euint64 newBalanceTo = FHE.add(balances[to], transferValue);
        balances[to] = newBalanceTo;
        FHE.allowThis(newBalanceTo);
        FHE.allow(newBalanceTo, to);

        // Update sender
        euint64 newBalanceFrom = FHE.sub(balances[from], transferValue);
        balances[from] = newBalanceFrom;
        FHE.allowThis(newBalanceFrom);
        FHE.allow(newBalanceFrom, from);

        emit Transfer(from, to);
    }

    // Balance is encrypted — only authorized addresses can decrypt
    function balanceOf(address wallet) public view returns (euint64) {
        return balances[wallet];
    }
}
```

**Key design decisions:**
- `_totalSupply` is plaintext — hiding market cap is usually not needed
- `decimals` is `6` (like USDC) — `euint64` max is ~18.4 quintillion, plenty for 6-decimal tokens
- `Transfer` event has no amount — this is intentional, not a bug
- Failed transfers are silent no-ops (transfer 0) — the contract doesn't revert, preserving privacy about whether the sender had sufficient balance

---

## 2. Encrypted Voting

Votes are encrypted. Nobody sees individual votes. Tally is revealed after the deadline.

```solidity
contract ConfidentialVoting is ZamaEthereumConfig {
    euint64 public encryptedYesCount;
    euint64 public encryptedNoCount;
    mapping(address => bool) public hasVoted;
    uint256 public deadline;
    bool public revealed;

    constructor(uint256 _duration) {
        deadline = block.timestamp + _duration;
        encryptedYesCount = FHE.asEuint64(0);
        encryptedNoCount = FHE.asEuint64(0);
        FHE.allowThis(encryptedYesCount);
        FHE.allowThis(encryptedNoCount);
    }

    function vote(
        externalEbool encryptedVote,  // true = yes, false = no
        bytes calldata inputProof
    ) public {
        require(block.timestamp < deadline, "Voting ended");
        require(!hasVoted[msg.sender], "Already voted");
        hasVoted[msg.sender] = true;

        ebool isYes = FHE.fromExternal(encryptedVote, inputProof);

        // Add 1 to yes or no count based on encrypted vote
        // Both branches execute — observer can't tell which
        euint64 one = FHE.asEuint64(1);
        euint64 zero = FHE.asEuint64(0);

        euint64 yesIncrement = FHE.select(isYes, one, zero);
        euint64 noIncrement = FHE.select(isYes, zero, one);

        encryptedYesCount = FHE.add(encryptedYesCount, yesIncrement);
        encryptedNoCount = FHE.add(encryptedNoCount, noIncrement);

        FHE.allowThis(encryptedYesCount);
        FHE.allowThis(encryptedNoCount);
    }

    function reveal() public {
        require(block.timestamp >= deadline, "Voting not ended");
        require(!revealed, "Already revealed");
        revealed = true;

        // Make results publicly decryptable
        FHE.makePubliclyDecryptable(encryptedYesCount);
        FHE.makePubliclyDecryptable(encryptedNoCount);
    }
}
```

**Key points:**
- Individual votes are never revealed — only the totals
- `FHE.select` ensures both counters are always updated (preventing gas analysis)
- Results are only decryptable after `reveal()` is called post-deadline

---

## 3. Sealed-Bid Auction

Bids are encrypted. Winner determined by FHE comparison. Losers refunded.

```solidity
contract SealedBidAuction is ZamaEthereumConfig {
    euint64 public highestBid;
    address public highestBidder;
    mapping(address => euint64) public bids;
    mapping(address => uint256) public deposits;  // Plaintext ETH deposits
    uint256 public deadline;
    bool public settled;

    constructor(uint256 _duration) {
        deadline = block.timestamp + _duration;
        highestBid = FHE.asEuint64(0);
        FHE.allowThis(highestBid);
    }

    function bid(
        externalEuint64 encryptedBid,
        bytes calldata inputProof
    ) public payable {
        require(block.timestamp < deadline, "Auction ended");
        require(bids[msg.sender].length == 0 || !FHE.isInitialized(bids[msg.sender]), "Already bid");

        euint64 bidAmount = FHE.fromExternal(encryptedBid, inputProof);
        bids[msg.sender] = bidAmount;
        deposits[msg.sender] = msg.value; // ETH deposit covers the bid

        FHE.allowThis(bidAmount);
        FHE.allow(bidAmount, msg.sender);

        // Update highest bid using encrypted comparison
        ebool isHigher = FHE.gt(bidAmount, highestBid);
        highestBid = FHE.select(isHigher, bidAmount, highestBid);
        FHE.allowThis(highestBid);

        emit BidPlaced(msg.sender);
    }

    function settle() public {
        require(block.timestamp >= deadline, "Auction not ended");
        require(!settled, "Already settled");
        settled = true;

        // Reveal the winning bid
        FHE.makePubliclyDecryptable(highestBid);
    }

    event BidPlaced(address indexed bidder);
}
```

**Note:** This is a simplified pattern. A production auction needs:
- Proper winner identification (tracking which bidder had the highest bid)
- Refund mechanism for losing bidders
- Deposit validation (ensuring deposits cover the encrypted bid)

---

## 4. Encrypted Counter / Accumulator

Simple pattern for tracking encrypted running totals.

```solidity
contract ConfidentialCounter is ZamaEthereumConfig {
    euint64 private counter;

    constructor() {
        counter = FHE.asEuint64(0);
        FHE.allowThis(counter);
    }

    function increment(
        externalEuint64 encryptedAmount,
        bytes calldata inputProof
    ) public {
        euint64 amount = FHE.fromExternal(encryptedAmount, inputProof);
        counter = FHE.add(counter, amount);
        FHE.allowThis(counter);
        // Grant access to whoever should be able to read it
    }

    function revealCounter() public {
        FHE.makePubliclyDecryptable(counter);
    }
}
```

---

## Pattern Checklist

For every pattern you implement:

- [ ] ACL: `FHE.allowThis()` after every encrypted state update
- [ ] ACL: `FHE.allow(value, user)` for every user who should read a value
- [ ] Branching: `FHE.select()` instead of `if` for encrypted conditions
- [ ] Events: no encrypted values in event parameters
- [ ] Inputs: `FHE.fromExternal()` to validate all user-submitted encrypted values
- [ ] Initialization: `FHE.isInitialized()` check before operating on potentially unset values
- [ ] View: no `view` modifier on functions that perform FHE operations
