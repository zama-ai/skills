---
name: zama-solidity
description: Guide for building confidential smart contracts on Zama's fhEVM. Triggers when user mentions confidential, private, encrypted, FHE, or secret contracts/tokens/data. Covers ERC-7984 confidential tokens, ACL, encrypted types, and Hardhat/Foundry test setup.
---

# Zama Solidity Skill

## How to use this skill

This skill is split into a small router (this file) plus reference files. Read **only** what the task needs:

1. **Always** read this file — it covers config, the ERC-7984 token recipe, and what the standard provides.
2. Pick a build/test environment and read **one** setup file. If the user does not specify, **default to Foundry**:
   - Foundry (default) → `setups/foundry.md`
   - Hardhat → `setups/hardhat.md`
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

## Gotchas (read before writing any FHE code)

- **Setup**: inherit `ZamaEthereumConfig`. Foundry needs `via_ir = true`; Hardhat does not.
- **Default type**: `euint64` for balances. `euint256` is dramatically more expensive per op.
- **Confidentiality**: `FHE.fromExternal()` is real encryption. `FHE.asEuintX(plaintext)` is **visible onchain** — constants only.
- **No `view`**: FHE ops are state-changing (coprocessor calls).
- **Control flow**: `ebool` cannot go in `if`/`require`/`while`. Use `FHE.select(cond, ifTrue, ifFalse)` — both branches must be encrypted values (materialise `FHE.asEuint64(0)`, not a literal), and both branches always execute (rejected paths still pay for their transfers/ops).
- **No encrypted divisor**: `FHE.div`/`FHE.rem` only accept a **plaintext** divisor. Redesign any formula with encrypted state in the divisor.
- **ACL (#1 bug)**: call `FHE.allowThis()` after creating/computing encrypted values, or the contract can't use them on the next call — silent failure, no revert. `ERC7984` handles this internally; only hand-written FHE code needs it. For single-tx cross-contract handles prefer `FHE.allowTransient` over persistent `FHE.allow`.
- **Input ciphertexts bind to one target contract**: `encryptUint64(value, user, target)` ties the proof to exactly `target`. Every hop needs its own encryption. Wrong target → runtime ACL revert with no compile hint.
- **Events**: never emit encrypted values — handle changes leak mutation timing. Emit addresses only.
- **Silent failures**: on insufficient balance FHE contracts transfer 0 via `FHE.select` — no revert. Test the zero-transfer case and call every function twice to prove ACL.
- **Public decrypt must be re-marked**: after every update to a publicly-decryptable state var, re-call `FHE.makePubliclyDecryptable(handle)`.
- **Decryption**: async Gateway in production; `decrypt`, `userDecrypt`, etc. are test-only helpers and don't exist on production `FHE.sol`. Make decryption the last step — no conditional actions after.
- **Info leaks**: reverting on an encrypted condition reveals it. Same for conditional events, differing return values, or gas differences tied to encrypted state.
- **Overloaded ERC-7984 functions**: call with explicit signature, e.g. `token["confidentialTransfer(address,bytes32,bytes)"](...)`.
- **HCU limits**: per-tx 20M, sequential depth 5M, per-block 5M. Prefer scalar operands, smallest type that fits, split functions over 10M. Full tables: https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md
- **Standard Solidity still applies**: CEI + `nonReentrant`, SafeERC20, access control, no hardcoded `1e18` (ERC-7984 uses **6** decimals), Sepolia before mainnet.

## Sources

- **HCU costs:** https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md
- **Zama Docs:** https://docs.zama.ai
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
- **Zama dApps (examples):** https://github.com/zama-ai/dapps/tree/main/packages/hardhat/contracts
- **Protocol Apps (deployed):** https://github.com/zama-ai/protocol-apps/tree/main/contracts
