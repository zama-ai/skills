---
name: addresses
description: Verified FHEVM and Zama protocol contract addresses across all supported chains. Use this instead of guessing or hallucinating addresses. Source — github.com/zama-ai/protocol-apps and ZamaConfig.sol.
---

# Contract Addresses

## What You Probably Got Wrong

**You guessed the coprocessor address.** Wrong address = silent ACL failures or reverted FHE operations. Always use `ZamaEthereumConfig` or reference verified addresses from this file.

**You hardcoded addresses instead of using ZamaEthereumConfig.** The config contract handles chain detection automatically. Hardcoding is fragile and breaks when addresses change.

**You didn't know about the confidential wrapper tokens.** Zama has deployed confidential wrappers for major tokens (cUSDC, cUSDT, cWETH, etc.). You don't need to build your own confidential ERC-20 for these — just use the official wrappers.

---

## Recommended: Use ZamaEthereumConfig for Configuration on Ethereum

```solidity
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaConfig.sol";

contract MyContract is ZamaEthereumConfig {
    // Automatically configures the correct ACL, Coprocessor, and KMSVerifier for:
    // - Ethereum mainnet (chainId=1)
    // - Sepolia testnet (chainId=11155111)
    // - Local development (chainId=31337)
}
```

**This is the preferred approach.** Only reference addresses below if you need manual configuration or need to interact with protocol contracts directly.

---

## FHEVM Core Infrastructure

These are the contracts that make FHE operations work. Configured automatically by `ZamaEthereumConfig`.

### Ethereum Mainnet (chainId=1)

| Contract | Address |
|----------|---------|
| ACL | [`0xcA2E8f1F656CD25C01F05d0b243Ab1ecd4a8ffb6`](https://etherscan.io/address/0xcA2E8f1F656CD25C01F05d0b243Ab1ecd4a8ffb6) |
| Coprocessor | [`0xD82385dADa1ae3E969447f20A3164F6213100e75`](https://etherscan.io/address/0xD82385dADa1ae3E969447f20A3164F6213100e75) |
| KMSVerifier | [`0x77627828a55156b04Ac0DC0eb30467f1a552BB03`](https://etherscan.io/address/0x77627828a55156b04Ac0DC0eb30467f1a552BB03) |

### Sepolia Testnet (chainId=11155111)

| Contract | Address |
|----------|---------|
| ACL | [`0xf0Ffdc93b7E186bC2f8CB3dAA75D86d1930A433D`](https://sepolia.etherscan.io/address/0xf0Ffdc93b7E186bC2f8CB3dAA75D86d1930A433D) |
| Coprocessor | [`0x92C920834Ec8941d2C77D188936E1f7A6f49c127`](https://sepolia.etherscan.io/address/0x92C920834Ec8941d2C77D188936E1f7A6f49c127) |
| KMSVerifier | [`0xbE0E383937d564D7FF0BC3b46c51f0bF8d5C311A`](https://sepolia.etherscan.io/address/0xbE0E383937d564D7FF0BC3b46c51f0bF8d5C311A) |

### Local Development (chainId=31337)

| Contract | Address |
|----------|---------|
| ACL | `0x50157CFfD6bBFA2DECe204a89ec419c23ef5755D` |
| Coprocessor | `0xe3a9105a3a932253A70F126eb1E3b589C643dD24` |
| KMSVerifier | `0x901F8942346f7AB3a01F6D7613119Bca447Bb030` |

---

## Confidential Wrapper Tokens

Official confidential wrappers for major ERC-20 tokens. These wrap a standard token into a confidential version with encrypted balances. **Use these instead of building your own confidential ERC-20 for these tokens.**

### Ethereum Mainnet

| Name | Symbol | Address |
|------|--------|---------|
| Confidential USDC | `cUSDC` | [`0xe978F22157048E5DB8E5d07971376e86671672B2`](https://etherscan.io/address/0xe978F22157048E5DB8E5d07971376e86671672B2) |
| Confidential USDT | `cUSDT` | [`0xAe0207C757Aa2B4019Ad96edD0092ddc63EF0c50`](https://etherscan.io/address/0xAe0207C757Aa2B4019Ad96edD0092ddc63EF0c50) |
| Confidential WETH | `cWETH` | [`0xda9396b82634Ea99243cE51258B6A5Ae512D4893`](https://etherscan.io/address/0xda9396b82634Ea99243cE51258B6A5Ae512D4893) |
| Confidential BRON | `cBRON` | [`0x85dE671c3bec1aDeD752c3Cea943521181C826bc`](https://etherscan.io/address/0x85dE671c3bec1aDeD752c3Cea943521181C826bc) |
| Confidential ZAMA | `cZAMA` | [`0x80CB147Fd86dC6dEe3Eee7e4Cee33d1397d98071`](https://etherscan.io/address/0x80CB147Fd86dC6dEe3Eee7e4Cee33d1397d98071) |
| Confidential tGBP | `ctGBP` | [`0xa873750ccBafD5ec7Dd13bfD5237d7129832eDD9`](https://etherscan.io/address/0xa873750ccBafD5ec7Dd13bfD5237d7129832eDD9) |
| Confidential XAUt | `cXAUt` | [`0x73cc9aF9d6BEFdb3c3fAf8a5E8c05Cb95FdaEEf1`](https://etherscan.io/address/0x73cc9aF9d6BEFdb3c3fAf8a5E8c05Cb95FdaEEf1) |

**Wrappers Registry:** [`0xeb5015fF021DB115aCe010f23F55C2591059bBA0`](https://etherscan.io/address/0xeb5015fF021DB115aCe010f23F55C2591059bBA0)

### Sepolia Testnet (Mock Wrappers)

Testnet wrappers use mocked mintable ERC-20 tokens as underlying. Find the underlying address via each wrapper's `underlying()` view function.

| Name | Symbol | Address |
|------|--------|---------|
| Confidential USDC (Mock) | `cUSDCMock` | [`0x7c5BF43B851c1dff1a4feE8dB225b87f2C223639`](https://sepolia.etherscan.io/address/0x7c5BF43B851c1dff1a4feE8dB225b87f2C223639) |
| Confidential USDT (Mock) | `cUSDTMock` | [`0x4E7B06D78965594eB5EF5414c357ca21E1554491`](https://sepolia.etherscan.io/address/0x4E7B06D78965594eB5EF5414c357ca21E1554491) |
| Confidential WETH (Mock) | `cWETHMock` | [`0x46208622DA27d91db4f0393733C8BA082ed83158`](https://sepolia.etherscan.io/address/0x46208622DA27d91db4f0393733C8BA082ed83158) |
| Confidential BRON (Mock) | `cBRONMock` | [`0xaa5612FA27c927a0c7961f5AEFEE5ba3A0F9C891`](https://sepolia.etherscan.io/address/0xaa5612FA27c927a0c7961f5AEFEE5ba3A0F9C891) |
| Confidential ZAMA (Mock) | `cZAMAMock` | [`0xf2D628d2598aF4eAF94CB76a437Ff86CA78FfbFB`](https://sepolia.etherscan.io/address/0xf2D628d2598aF4eAF94CB76a437Ff86CA78FfbFB) |
| Confidential tGBP (Mock) | `ctGBPMock` | [`0xfCE5c7069c5525eF6c8C2b2E35A745bA20a2F7CC`](https://sepolia.etherscan.io/address/0xfCE5c7069c5525eF6c8C2b2E35A745bA20a2F7CC) |
| Confidential XAUt (Mock) | `cXAUtMock` | [`0xe4FcF848739845BC81Dee1d5352cf3844F0a60C7`](https://sepolia.etherscan.io/address/0xe4FcF848739845BC81Dee1d5352cf3844F0a60C7) |
| Confidential tGBP | `ctGBP` | [`0x167DC962808B32CFFFc7e14B5018c0bE06A3A208`](https://sepolia.etherscan.io/address/0x167DC962808B32CFFFc7e14B5018c0bE06A3A208) |

**Wrappers Registry (Sepolia):** [`0x2f0750Bbb0A246059d80e94c454586a7F27a128e`](https://sepolia.etherscan.io/address/0x2f0750Bbb0A246059d80e94c454586a7F27a128e)

---

## ZAMA Token

### Ethereum Mainnet

| Name | Address |
|------|---------|
| Zama Token | [`0xA12CC123ba206d4031D1c7f6223D1C2Ec249f4f3`](https://etherscan.io/address/0xA12CC123ba206d4031D1c7f6223D1C2Ec249f4f3) |
| Zama OFT Adapter | [`0xa798B04149e7a61cc95B7D114AD420e8969eA268`](https://etherscan.io/address/0xa798B04149e7a61cc95B7D114AD420e8969eA268) |

### Sepolia Testnet

| Name | Address |
|------|---------|
| Zama Token | [`0xa798B04149e7a61cc95B7D114AD420e8969eA268`](https://sepolia.etherscan.io/address/0xa798B04149e7a61cc95B7D114AD420e8969eA268) |
| Zama OFT Adapter | [`0x55D5258841e9Fd304007683ff4637b0a80fb0e62`](https://sepolia.etherscan.io/address/0x55D5258841e9Fd304007683ff4637b0a80fb0e62) |

### Other Chains

| Chain | Contract | Address |
|-------|----------|---------|
| BSC Mainnet | Zama OFT | [`0x6907A5986C4950Bdaf2F81828Ec0737ce787519f`](https://bscscan.com/address/0x6907a5986c4950bdaf2f81828ec0737ce787519f) |
| HyperEVM Mainnet | Zama OFT | [`0x43cdd2cCbeB38Eb62fDf54e17aFBabf450ebBB01`](https://hyperevmscan.io/address/0x43cdd2cCbeB38Eb62fDf54e17aFBabf450ebBB01) |
| HyperEVM Mainnet | HyperLiquid Composer | [`0x7B19Dc1d968756D895f7aA4273e174D45F8C87F0`](https://hyperevmscan.io/address/0x7B19Dc1d968756D895f7aA4273e174D45F8C87F0) |
| Gateway Mainnet | Zama OFT | [`0xcE762c7FDaac795D31a266B9247F8958c159c6d4`](https://explorer.mainnet.zama.org/address/0xcE762c7FDaac795D31a266B9247F8958c159c6d4) |
| Gateway Testnet | Zama OFT | [`0xcE762c7FDaac795D31a266B9247F8958c159c6d4`](https://explorer.testnet.zama.org/address/0xcE762c7FDaac795D31a266B9247F8958c159c6d4) |
| Solana Mainnet | Zama OFT (Mint) | [`4Zp52aF4hZi9fzH19xpbWKYKQvgLyCN67KFbrQDqeTKh`](https://explorer.solana.com/address/4Zp52aF4hZi9fzH19xpbWKYKQvgLyCN67KFbrQDqeTKh) |
| Solana Mainnet | Zama OFT Program | [`A8W6AL4JhE4EDDcfXZ1Q8vQpwp83AnPj4UZ6y86gVFKN`](https://explorer.solana.com/address/A8W6AL4JhE4EDDcfXZ1Q8vQpwp83AnPj4UZ6y86gVFKN) |

---

## Staking

### Ethereum Mainnet — Protocol Staking

| Role | Address |
|------|---------|
| KMS | [`0xe9b176CCaA8840DC3b3567bb83e2cD2a6c36F4Ab`](https://etherscan.io/address/0xe9b176CCaA8840DC3b3567bb83e2cD2a6c36F4Ab) |
| Coprocessor | [`0x7147485b892158f2B875f7aC5Ea48A9937C66AE8`](https://etherscan.io/address/0x7147485b892158f2B875f7aC5Ea48A9937C66AE8) |

### Sepolia — Protocol Staking

| Role | Address |
|------|---------|
| KMS | [`0x0309b4308A6AC121B9b3A960aC7Bc9bd8256cf38`](https://sepolia.etherscan.io/address/0x0309b4308A6AC121B9b3A960aC7Bc9bd8256cf38) |
| Coprocessor | [`0xc22E393D2A1C1BD65c88d34a3bE4DD77e8952E71`](https://sepolia.etherscan.io/address/0xc22E393D2A1C1BD65c88d34a3bE4DD77e8952E71) |

---

## Governance

### Ethereum Mainnet

| Name | Address |
|------|---------|
| Protocol DAO | [`0xB6D69D5F334d8B97B194617B53c6aB62f8681Ef3`](https://etherscan.io/address/0xB6D69D5F334d8B97B194617B53c6aB62f8681Ef3) |
| Governance Multisig | [`0xE43c73aAb2b6aBBad6d0461997ce1cfea5ABe66f`](https://etherscan.io/address/0xE43c73aAb2b6aBBad6d0461997ce1cfea5ABe66f) |
| Governance OApp Sender | [`0x1c5D750D18917064915901048cdFb2dB815e0910`](https://etherscan.io/address/0x1c5D750D18917064915901048cdFb2dB815e0910) |

### Gateway Mainnet

| Name | Address |
|------|---------|
| Governance OApp Receiver | [`0x10795261A06285D3718674a9Cf98Ea66F7C6A0c6`](https://explorer.mainnet.zama.org/address/0x10795261A06285D3718674a9Cf98Ea66F7C6A0c6) |
| Admin Module | [`0x57f866b5E7Fb82Fb812Ed3D3C79cdB35E9e91518`](https://explorer.mainnet.zama.org/address/0x57f866b5E7Fb82Fb812Ed3D3C79cdB35E9e91518) |
| Safe Multisig | [`0x5f0F86BcEad6976711C9B131bCa5D30E767fe2bE`](https://explorer.mainnet.zama.org/address/0x5f0F86BcEad6976711C9B131bCa5D30E767fe2bE) |

---

## Pausing

| Chain | Name | Address |
|-------|------|---------|
| Ethereum Mainnet | Pauser Set | [`0xbBfE1680b4a63ED05f7F80CE330BED7C992A586C`](https://etherscan.io/address/0xbBfE1680b4a63ED05f7F80CE330BED7C992A586C) |
| Ethereum Mainnet | Pauser Set Wrapper (minting) | [`0x08940bC8944A17E64AA9F5398046ABc75bB26699`](https://etherscan.io/address/0x08940bC8944A17E64AA9F5398046ABc75bB26699) |
| Gateway Mainnet | Pauser Set | [`0x571ecb596fCc5c840DA35CbeCA175580db50ac1b`](https://explorer.mainnet.zama.org/address/0x571ecb596fCc5c840DA35CbeCA175580db50ac1b) |
| Sepolia | Pauser Set | [`0xc62392B4100a1bD45AbDBf91E70f1E4349402b46`](https://sepolia.etherscan.io/address/0xc62392B4100a1bD45AbDBf91E70f1E4349402b46) |
| Sepolia | Pauser Set Wrapper (minting) | [`0xEd03Be6711787f3068885137723504a075514040`](https://sepolia.etherscan.io/address/0xEd03Be6711787f3068885137723504a075514040) |
| Gateway Testnet | Pauser Set | [`0x057dC9855536470A6D8C21d075bA17EA062A5dE7`](https://explorer.testnet.zama.org/address/0x057dC9855536470A6D8C21d075bA17EA062A5dE7) |

---

## Block Explorers

| Chain | Explorer |
|-------|----------|
| Ethereum Mainnet | https://etherscan.io |
| Sepolia Testnet | https://sepolia.etherscan.io |
| BSC Mainnet | https://bscscan.com |
| HyperEVM Mainnet | https://hyperevmscan.io |
| Gateway Mainnet | https://explorer.mainnet.zama.org |
| Gateway Testnet | https://explorer.testnet.zama.org |
| Solana Mainnet | https://explorer.solana.com |

---

## Verifying Addresses

```bash
# Check that a contract exists at the address
cast code 0xcA2E8f1F656CD25C01F05d0b243Ab1ecd4a8ffb6 --rpc-url https://eth.llamarpc.com

# If cast returns "0x" (empty), the address has no contract — something is wrong
```

**Never trust addresses from LLM memory alone.** Addresses can change between versions. Always verify against the latest `@fhevm/solidity` package or the [official addresses repo](https://github.com/zama-ai/protocol-apps/tree/main/docs/addresses).

---

## Sources

- **ZamaConfig.sol:** `@fhevm/solidity/config/ZamaConfig.sol` — [source](https://github.com/zama-ai/fhevm/blob/main/library-solidity/config/ZamaConfig.sol)
- **Protocol addresses:** https://github.com/zama-ai/protocol-apps/tree/main/docs/addresses
- **Zama Documentation:** https://docs.zama.ai/protocol
