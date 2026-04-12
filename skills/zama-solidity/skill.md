---
name: zama-solidity
description: Guide for building confidential smart contracts on Zama's fhEVM. Triggers when user mentions confidential, private, encrypted, FHE, or secret contracts/tokens/data. Covers ERC-7984 confidential tokens, ACL, encrypted types, and Hardhat/Foundry test setup.
---

# Zama Solidity Skill

## How to use this skill

This skill is split into a small router (this file) plus reference files. Read **only** what the task needs:

1. **Always** read this file — it covers config, the ERC-7984 token recipe, and what the standard provides.
2. Pick a build/test environment and read **one** setup file:
   - Hardhat → `setups/hardhat.md`
   - Foundry → `setups/foundry.md`
3. Read `references/fhe-advanced.md` **only if** you go beyond `ERC7984`'s built-ins — i.e. you write FHE arithmetic or comparisons yourself, manage ACL by hand, do production decryption, or use raw encrypted types. For a plain mint/burn/transfer token you do NOT need it.

## Configuration

**Always inherit `ZamaEthereumConfig`** — it sets the correct FHE coprocessor addresses (ACL, FHEVMExecutor, KMSVerifier) per `block.chainid`. Supported: Ethereum mainnet, Sepolia, local Hardhat (31337).

## Confidential Tokens: Use ERC-7984

When the user wants a confidential token (encrypted ERC20, private-balance token, FHE token), **use the ERC-7984 standard from OpenZeppelin's confidential contracts library**. Never reimplement encrypted balances/allowances/transfers.

- Repo: https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
- Standard: ERC-7984, the confidential fungible token interface for fhEVM

## Mintable & Burnable Confidential Token

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.27;

import {FHE, externalEuint64} from "@fhevm/solidity/lib/FHE.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ERC7984} from "@openzeppelin/confidential-contracts/token/ERC7984/ERC7984.sol";
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaConfig.sol";

contract MyConfidentialToken is ERC7984, Ownable, ZamaEthereumConfig {
    constructor(
        address owner,
        string memory name_,
        string memory symbol_,
        string memory uri_
    ) ERC7984(name_, symbol_, uri_) Ownable(owner) {}

    function mint(address to, externalEuint64 amount, bytes memory proof) external onlyOwner {
        _mint(to, FHE.fromExternal(amount, proof));
    }

    function burn(address from, externalEuint64 amount, bytes memory proof) external onlyOwner {
        _burn(from, FHE.fromExternal(amount, proof));
    }
}
```

## What ERC-7984 provides

| Function | Description |
|---|---|
| `confidentialTransfer(to, encAmount, proof)` | Transfer with encrypted input |
| `confidentialTransferFrom(from, to, encAmount, proof)` | Operator/delegated transfer |
| `confidentialTransferAndCall(...)` | Transfer + receiver hook (ERC-7984 Receiver) |
| `confidentialBalanceOf(account)` | Returns encrypted balance handle |
| `confidentialTotalSupply()` | Returns encrypted total supply |
| `setOperator(operator, until)` / `isOperator(...)` | Time-bound operator approvals |
| `requestDiscloseEncryptedAmount(amount)` | Request decryption disclosure |
| `discloseEncryptedAmount(amount, cleartext, proof)` | Verify and disclose a decrypted amount |
| `name()` / `symbol()` / `decimals()` (= **6**, not 18) / `contractURI()` | Standard metadata |

### Extensions (under `@openzeppelin/confidential-contracts/token/ERC7984/extensions/`)

| Extension | Purpose |
|---|---|
| `ERC7984Freezable` | Freeze/unfreeze accounts |
| `ERC7984Restricted` | Transfer restrictions |
| `ERC7984ObserverAccess` | Read access for observers |
| `ERC7984Omnibus` | Omnibus accounts |
| `ERC7984Rwa` | Real-world asset features |
| `ERC7984Votes` | Governance voting on encrypted balances |
| `ERC7984ERC20Wrapper` | Wrap an existing ERC20 into ERC-7984 |

## Example projects

- https://github.com/zama-ai/protocol-apps/tree/main/contracts — production contracts
- https://github.com/zama-ai/dapps — full confidential dApps with frontends

## Quick Reference

- **Setup**: inherit `ZamaEthereumConfig`. Foundry needs `via_ir = true`; Hardhat does not.
- **Confidentiality**: `FHE.fromExternal()` is real encryption. `FHE.asEuintX(plaintext)` is **not** confidential.
- **ACL**: call `FHE.allowThis()` after creating/computing encrypted values (only relevant if you write FHE ops yourself — `ERC7984` handles this internally).
- **Control flow**: `ebool` cannot go in an `if`. Use `FHE.select(cond, ifTrue, ifFalse)`.
- **Decryption**: async Gateway in production; test helpers (`decrypt`, `userDecrypt`, etc.) do **not** exist on production `FHE.sol`.
- **Common error**: ERC-7984 has overloaded functions — call with explicit signature, e.g. `token["confidentialTransfer(address,bytes32,bytes)"](...)`.
