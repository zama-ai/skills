# Foundry setup for fhEVM

Use **forge-fhevm** — bundles `openzeppelin-confidential-contracts`, `fhevm-solidity`, `encrypted-types`, and the `FhevmTest` framework.

- Repo: https://github.com/zama-ai/forge-fhevm

## Install

```bash
forge install zama-ai/forge-fhevm
forge remappings > remappings.txt
```

## foundry.toml

```toml
[profile.default]
evm_version = "cancun"
via_ir = true
optimizer = true
optimizer_runs = 200
```

**`via_ir = true` is mandatory** — FHE contracts hit "stack too deep" without it.

## Test pattern

Inherit `FhevmTest`. `setUp()` deploys real fhEVM host contracts at canonical addresses.

```solidity
import {FhevmTest} from "forge-fhevm/FhevmTest.sol";
import {euint64, externalEuint64} from "@fhevm/solidity/lib/FHE.sol";

contract MyTokenTest is FhevmTest {
    uint256 internal constant OWNER_PK = 0xA11CE;
    uint256 internal constant USER_PK = 0xB0B;

    MyConfidentialToken internal token;

    function setUp() public override {
        super.setUp();
        address owner = vm.addr(OWNER_PK);
        vm.prank(owner);
        token = new MyConfidentialToken(owner, "Token", "TKN", "https://x");
    }

    function test_mint() public {
        address owner = vm.addr(OWNER_PK);
        address user = vm.addr(USER_PK);

        (externalEuint64 amount, bytes memory proof) = encryptUint64(1000, owner, address(token));
        vm.prank(owner);
        token.mint(user, amount, proof);

        euint64 balance = token.confidentialBalanceOf(user);
        bytes memory sig = signUserDecrypt(USER_PK, address(token));
        uint256 clear = userDecrypt(euint64.unwrap(balance), user, address(token), sig);
        assertEq(clear, 1000);
    }
}
```

## FhevmTest helpers

| Helper | Purpose |
|---|---|
| `encryptUint64(value, user, target)` | Encrypted input + proof (also `encryptBool`, `encryptUint8`–`encryptUint256`, `encryptAddress`) |
| `decrypt(handle)` | Direct decrypt — skips ACL, fastest for assertions |
| `userDecrypt(handle, user, contract, sig)` | Full ACL + EIP-712 user decrypt |
| `signUserDecrypt(pk, contract)` | Sign a user decrypt request |
| `publicDecrypt(handles)` | Decrypt publicly marked handles |
| `dealConfidential(wrapper, user, amount)` | Fund user with wrapped ERC-7984 (like `deal`) |
