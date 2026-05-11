# Hardhat setup for FHEVM

Start from the template — it pins a coherent Hardhat + plugin + chai-matchers + ethers stack.

> **Template:** https://github.com/zama-ai/fhevm-hardhat-template

```bash
git clone https://github.com/zama-ai/fhevm-hardhat-template my-project
cd my-project && npm install
```

What follows is only the FHEVM-specific stuff you need to know that doesn't come from the template.

## Why rolling your own is risky

FHEVM currently supports **Hardhat V2 only**. Several packages in the Hardhat ecosystem ship Hardhat-3 builds on their `latest` tag, which silently breaks Hardhat-2 projects at install or compile time. The template pins:

- Hardhat at a v2 major
- `@nomicfoundation/hardhat-chai-matchers` at the `@hh2` variant (latest is Hardhat-3-only)
- `chai` at v4 (chai 5 is ESM-only, incompatible with the matchers)
- `ethers` v6 and `@nomicfoundation/hardhat-ethers` v3 (must match)

If you assemble the toolchain yourself, reproduce that pin strategy. Specific version numbers are intentionally not listed here — take them from the template.

## FHEVM-specific packages

`@fhevm/solidity`, `@fhevm/hardhat-plugin`, `@fhevm/mock-utils`, `@openzeppelin/confidential-contracts`, `encrypted-types`. These identifiers don't move across Hardhat versions.

## Config essentials

```typescript
import "@fhevm/hardhat-plugin"; // registers the `fhevm` runtime on `hre`
```

`tsconfig.json` must set `rootDir: "."` — otherwise `tsc` infers `./test` and errors with TS5011 once `typechain-types/` is generated.

Don't enable `viaIR` preemptively; turn it on only if `solc` reports "stack too deep."

## Tests

Pattern: `fhevm.createEncryptedInput(contract, user).addXX(value).encrypt()` → call contract → `fhevm.userDecryptEuint(FhevmType.euintXX, handle, contract, signer)`. Gate mock-only behaviour with `if (!fhevm.isMock) this.skip()`.

| Helper | Use |
|--------|-----|
| `fhevm.createEncryptedInput(contract, user).addXX(v).encrypt()` | `{ handles, inputProof }` — same shape as production SDK |
| `fhevm.userDecryptEuint(FhevmType.euintXX, handle, contract, signer)` | `bigint` — full ACL + EIP-712 simulation |
| `fhevm.isMock` | Gate mock-only assertions |

## Recurring gotchas

- **Overloaded ERC-7984 functions**: ethers can't disambiguate. Use the explicit signature: `token["confidentialTransfer(address,bytes32,bytes)"](to, handle, proof)`.
- **Stale build cache after upgrades**: nuke `cache/`, `artifacts/`, `typechain-types/` and recompile.
