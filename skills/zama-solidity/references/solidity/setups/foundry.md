# Foundry setup for FHEVM

Start from the template — it pins a coherent toolchain and `forge-fhevm` version.

> **Template:** https://github.com/zama-ai/fhevm-foundry-template

```bash
forge init my-project --template zama-ai/fhevm-foundry-template
```

What follows is only the FHEVM-specific stuff you need to know that doesn't come from the template.

## `forge-fhevm`

The Foundry-side support package ([repo](https://github.com/zama-ai/forge-fhevm)). Bundles `@fhevm/solidity`, `@openzeppelin/confidential-contracts`, `encrypted-types`, and `FhevmTest` (a test framework that deploys the real FHEVM host contracts at canonical addresses). If you're not using the template: `forge install zama-ai/forge-fhevm`.

## One mandatory `foundry.toml` entry

```toml
fs_permissions = [
    { access = "read-write", path = "lib/forge-fhevm/src/fhevm-host/addresses/FHEVMHostAddresses.sol" },
]
```

`FhevmTest.setUp()` writes the canonical host addresses to disk; without this, every test reverts with a filesystem-permission error.

Everything else (`solc` version, EVM version, optimizer, `via_ir`) — take what the template ships. Don't enable `via_ir` preemptively; turn it on only when `solc` actually reports "stack too deep."

## Tests

Inherit `FhevmTest` — `setUp()` deploys ACL, FHEVMExecutor, KMSVerifier, InputVerifier, HCULimit at canonical addresses, so tests run against the same surface as Sepolia/mainnet.

The test pattern is `encryptXxx → call contract → userDecrypt | decrypt | publicDecrypt`. Exact helper signatures evolve with `forge-fhevm` releases — check `lib/forge-fhevm/src/` in your project. Stable shape:

| Helper | Use |
|--------|-----|
| `encryptXxx(value, user, target)` | Build `{externalEuintN, proof}` bound to `target` |
| `decrypt(handle)` | ACL-skipping decrypt — fastest for assertions |
| `userDecrypt(handle, user, contract, sig)` | Full ACL + EIP-712 user-decrypt path |
| `signUserDecrypt(pk, contract)` | Sign a user-decrypt EIP-712 |
| `publicDecrypt(handles)` | Decrypt handles already marked publicly decryptable |
| `dealConfidential(wrapper, user, amount)` | Fund a user with wrapped ERC-7984 (`deal`-style) |
