---
name: setup
description: "Set up an FHEVM smart contract project. Use when users need to: (1) start a new encrypted contract project with Foundry or Hardhat, (2) add FHEVM to an existing project, (3) install forge-fhevm, openzeppelin-confidential-contracts, or fhevm-hardhat-template."
license: BSD-3-Clause-Clear
metadata:
  author: Zama
---

# FHEVM Solidity Setup

Two paths to start writing encrypted smart contracts. Detect the framework by looking for `hardhat.config.*` (Hardhat) or `foundry.toml` (Foundry). For new projects, ask the user which framework they prefer.

---

## Path 1: Foundry (forge-fhevm)

Clone the template or add to an existing Foundry project.

### New Project — Use the Template

```bash
git clone https://github.com/zama-ai/fhevm-foundry-template
cd fhevm-foundry-template
forge install
```

This template comes pre-configured with forge-fhevm, OpenZeppelin Contracts, and OpenZeppelin Confidential Contracts.

### Existing Project — Add Dependencies

```bash
# Core FHEVM support for Foundry
forge install zama-ai/forge-fhevm

# OpenZeppelin Confidential Contracts (ERC-7984, confidential tokens)
forge install OpenZeppelin/openzeppelin-confidential-contracts

# Standard OpenZeppelin Contracts (access control, SafeERC20, proxies)
forge install OpenZeppelin/openzeppelin-contracts
```

### Remappings

Add to `remappings.txt`:

```text
forge-fhevm/=lib/forge-fhevm/src/
@openzeppelin/contracts/=lib/openzeppelin-contracts/contracts/
@openzeppelin/confidential-contracts/=lib/openzeppelin-confidential-contracts/contracts/
```

### Verify Setup

```bash
forge build
```

---

## Path 2: Hardhat (fhevm-hardhat-template)

Clone the official Hardhat template — it comes with the FHEVM plugin, encrypted test helpers, and deployment scripts pre-configured.

### New Project — Use the Template

```bash
git clone https://github.com/zama-ai/fhevm-hardhat-template
cd fhevm-hardhat-template
npm install
```

### Verify Setup

```bash
npx hardhat compile
```

---

## First Contract

Regardless of framework, your first contract should look like this:

```solidity
// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.24;

import {FHE, euint64, externalEuint64} from "@fhevm/solidity/lib/FHE.sol";
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaConfig.sol";

contract MyFirstContract is ZamaEthereumConfig {
    euint64 private counter;

    constructor() {
        counter = FHE.asEuint64(0);
        FHE.allowThis(counter);
    }

    function add(externalEuint64 encryptedValue, bytes calldata inputProof) external {
        euint64 value = FHE.fromExternal(encryptedValue, inputProof);
        counter = FHE.add(counter, value);
        FHE.allowThis(counter);
        FHE.allow(counter, msg.sender);
    }
}
```

**Key points:**
- Always inherit `ZamaEthereumConfig` first
- `FHE.allowThis()` after every state update (ACL — the #1 bug source)
- User inputs come as `externalEuint64` + `inputProof`, converted via `FHE.fromExternal()`

---

## References

- [forge-fhevm](https://github.com/zama-ai/forge-fhevm) — Foundry library for FHEVM
- [fhevm-foundry-template](https://github.com/zama-ai/fhevm-foundry-template) — Foundry starter template
- [fhevm-hardhat-template](https://github.com/zama-ai/fhevm-hardhat-template) — Hardhat starter template
- [openzeppelin-confidential-contracts](https://github.com/OpenZeppelin/openzeppelin-confidential-contracts) — ERC-7984, confidential tokens

For ACL patterns, security vulnerabilities, HCU costs, and the pre-deploy checklist, see the main [solidity/SKILL.md](../SKILL.md).
