---
name: deployment
description: Deploying encrypted contracts to FHEVM-compatible chains. Chain configuration, testnet-first workflow, and post-deploy verification.
---

# Deployment — Shipping Encrypted Contracts

## What You Probably Got Wrong

**You deployed to mainnet without testing on Sepolia.** FHE operations consume real coprocessor resources and cost significantly more gas than regular operations. Test on Sepolia first — always.

**You forgot to inherit ZamaEthereumConfig.** Without it, the coprocessor isn't configured and all FHE operations fail silently or revert.

**You didn't verify the contract.** Encrypted contracts are harder to audit by users. Verification on the block explorer is more important, not less.

---

## Pre-Deployment Checklist

- [ ] Contract inherits `ZamaEthereumConfig` (or calls `FHE.setCoprocessor()`)
- [ ] All FHE operations tested on local mock (Hardhat)
- [ ] All ACL patterns verified (every state update has `allowThis` + `allow`)
- [ ] No `view` modifier on functions with FHE operations
- [ ] No encrypted values in events
- [ ] Security checklist from `security/SKILL.md` completed

---

## Chain Configuration

### Automatic (Recommended)

```solidity
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaConfig.sol";

contract MyContract is ZamaEthereumConfig {
    // Automatically configures for:
    // - Ethereum mainnet (chainId=1)
    // - Sepolia testnet (chainId=11155111)
}
```

### Manual

```solidity
import "@fhevm/solidity/lib/FHE.sol";
import {CoprocessorSetup} from "./CoprocessorSetup.sol";

contract MyContract {
    constructor() {
        FHE.setCoprocessor(CoprocessorSetup.defaultConfig());
    }
}
```

---

## Deployment Workflow

### 1. Deploy to Sepolia

```bash
# Deploy
npx hardhat run scripts/deploy.ts --network sepolia

# Verify
npx hardhat verify --network sepolia <CONTRACT_ADDRESS> "TokenName" "SYM"
```

### 2. Test on Sepolia

Run at least one end-to-end encrypted operation:

```
1. Mint tokens (plaintext amount → encrypted storage)
2. Transfer tokens (encrypted input → encrypted state update)
3. Decrypt balance (verify ACL works for authorized user)
4. Attempt unauthorized decrypt (verify it fails)
```

### 3. Deploy to Mainnet

```bash
npx hardhat run scripts/deploy.ts --network mainnet
npx hardhat verify --network mainnet <CONTRACT_ADDRESS> "TokenName" "SYM"
```

### 4. Post-Deploy Verification

```bash
# Verify contract has code
cast code <ADDRESS> --rpc-url https://eth.llamarpc.com

# Call a read function to verify deployment
cast call <ADDRESS> "name()(string)" --rpc-url https://eth.llamarpc.com

# Check that ZamaEthereumConfig resolved correctly
# (the contract should be able to perform FHE operations)
```

---

## Gas Considerations

FHE operations cost more gas than plaintext equivalents:

| Operation | Approximate Gas Cost |
|-----------|---------------------|
| `FHE.add(euint64, euint64)` | Higher than regular `+` |
| `FHE.mul(euint64, euint64)` | Significantly higher |
| `FHE.select(ebool, euint64, euint64)` | Higher than ternary |
| `FHE.allow()` | Storage write (ACL entry) |
| `FHE.allowTransient()` | Transient storage (cheaper) |

**Optimize by:**
- Using `euint64` instead of `euint256` where possible
- Using `allowTransient()` for temporary values
- Minimizing the number of FHE operations per transaction
- Keeping non-sensitive values as plaintext

---

## Production Hardening

### Transfer Ownership

```solidity
// After deployment, transfer ownership to a multisig
// Never leave a single EOA as owner in production
await contract.transferOwnership(multisigAddress);
// Then accept from the multisig (Ownable2Step)
```

### Monitor

- Watch for failed FHE operations in transaction traces
- Monitor gas costs — encrypted operations can spike
- Verify that decryption works for authorized users

---

## Resources

- **Sepolia faucet:** https://sepoliafaucet.com
- **Zama docs:** https://docs.zama.ai/protocol
- **Contract addresses:** Fetch `addresses/SKILL.md`
