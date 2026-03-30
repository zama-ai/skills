---
name: tools
description: The FHEVM development toolchain — Hardhat plugin, Solidity library, coprocessor, and what actually works today for building encrypted dApps.
---

# Tools — The FHEVM Development Stack

## What You Probably Got Wrong

**You tried to use Foundry.** FHEVM doesn't have Foundry support yet. Use Hardhat with the `fhevm-hardhat-plugin`.

**You imported from the wrong package.** The Solidity library is `@fhevm/solidity`. The Hardhat plugin is `@fhevm/hardhat-plugin`. Don't confuse them.

**You tried to run FHE operations locally without the plugin.** FHE operations require a coprocessor. The Hardhat plugin provides a local mock environment for testing.

---

## The Stack

```text
┌───────────────────────────────────────────────────┐
│  Your Contract (Solidity)                          │
│  imports @fhevm/solidity/lib/FHE.sol               │
├───────────────────────────────────────────────────┤
│  Hardhat + @fhevm/hardhat-plugin                   │
│  Local FHE mock for testing                        │
├───────────────────────────────────────────────────┤
│  FHEVM Host Contracts (onchain)                    │
│  ACL, FHEVMExecutor, KMSVerifier                   │
├───────────────────────────────────────────────────┤
│  Coprocessor (offchain)                            │
│  Rust FHE computation engine                       │
├───────────────────────────────────────────────────┤
│  KMS (Key Management Service)                      │
│  Holds decryption keys, handles key requests       │
└───────────────────────────────────────────────────┘
```

---

## Project Setup

### New Project

```bash
# Create a new Hardhat project with FHEVM
mkdir my-fhevm-project && cd my-fhevm-project
npm init -y
npm install --save-dev hardhat @fhevm/hardhat-plugin @fhevm/solidity
npx hardhat init
```

### hardhat.config.ts

```typescript
import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import "@fhevm/hardhat-plugin";

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  networks: {
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
    },
  },
};

export default config;
```

### Contract Imports

```solidity
// The main FHE library — all encrypted operations
import "@fhevm/solidity/lib/FHE.sol";

// Auto-configuration for Ethereum chains
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaConfig.sol";

// OpenZeppelin (for access control, etc.)
import "@openzeppelin/contracts/access/Ownable2Step.sol";
```

---

## Key Packages

| Package | Purpose | Install |
|---------|---------|---------|
| `@fhevm/solidity` | Solidity library (`FHE.sol`, configs) | `npm install @fhevm/solidity` |
| `@fhevm/hardhat-plugin` | Hardhat plugin for local FHE testing | `npm install --save-dev @fhevm/hardhat-plugin` |
| `@openzeppelin/contracts` | Standard Solidity utilities | `npm install @openzeppelin/contracts` |

---

## Development Workflow

```text
1. Write contract → import FHE.sol, inherit ZamaEthereumConfig
2. Write tests → use fhevm.createEncryptedInput() and fhevm.decrypt*()
3. Run tests → npx hardhat test (plugin provides mock FHE environment)
4. Deploy to Sepolia → npx hardhat run scripts/deploy.ts --network sepolia
5. Verify on explorer → npx hardhat verify --network sepolia <address>
6. Deploy to mainnet → same, with mainnet network config
```

### Running Tests

```bash
# Run all tests with mock FHE
npx hardhat test

# Run specific test file
npx hardhat test test/ConfidentialERC20.test.ts

# With gas reporting
REPORT_GAS=true npx hardhat test
```

### Deployment Script

```typescript
import { ethers } from "hardhat";

async function main() {
  const Factory = await ethers.getContractFactory("ConfidentialERC20");
  const contract = await Factory.deploy("My Token", "MTK");
  await contract.waitForDeployment();

  console.log("Deployed to:", await contract.getAddress());
}

main().catch(console.error);
```

---

## Client-Side (Frontend)

### Encrypting Inputs

```typescript
import { fhevm } from "hardhat"; // In tests
// For frontend, use the fhevmjs library

const input = fhevm.createEncryptedInput(contractAddress, userAddress);
input.add64(amount);      // Add a uint64 value
input.addBool(flag);      // Add a bool value
const encrypted = await input.encrypt();

// Submit to contract
await contract.myFunction(
  encrypted.handles[0],   // First encrypted value
  encrypted.handles[1],   // Second encrypted value
  encrypted.inputProof    // Proof covering all inputs
);
```

---

## Useful Links

- **Zama Documentation:** https://docs.zama.ai/protocol
- **FHEVM Repository:** https://github.com/zama-ai/fhevm
- **FHEVM Solidity Library:** npm `@fhevm/solidity`
- **Hardhat Plugin:** npm `@fhevm/hardhat-plugin`
- **Example Contracts:** https://github.com/zama-ai/fhevm/tree/main/examples
