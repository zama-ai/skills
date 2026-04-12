# Hardhat setup for fhEVM

fhEVM currently supports **Hardhat V2 only** (`@nomicfoundation/hardhat-chai-matchers` latest is Hardhat 3 — must use the `@hh2` tag).

## Install

```bash
npm init -y
npm install --save-dev hardhat@^2.28.4 @fhevm/hardhat-plugin @fhevm/mock-utils \
  @nomicfoundation/hardhat-chai-matchers@hh2 @nomicfoundation/hardhat-ethers@^3.0.0 \
  @typechain/hardhat @typechain/ethers-v6 typechain \
  typescript ts-node @types/node @types/mocha @types/chai chai@^4 ethers@^6
npm install @fhevm/solidity encrypted-types @openzeppelin/confidential-contracts @openzeppelin/contracts
```

Pinning notes:
- `@nomicfoundation/hardhat-chai-matchers@hh2` — the plain `latest` tag installs a Hardhat-3-only build that errors at compile time.
- `chai@^4` — Hardhat 2 / chai-matchers do not work with chai 5 (ESM).
- `ethers@^6` + `@nomicfoundation/hardhat-ethers@^3` — must match.

## hardhat.config.ts

```typescript
import "@fhevm/hardhat-plugin";
import "@nomicfoundation/hardhat-chai-matchers";
import "@nomicfoundation/hardhat-ethers";
import "@typechain/hardhat";
import type { HardhatUserConfig } from "hardhat/config";

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.27",
    settings: {
      optimizer: { enabled: true, runs: 800 },
      evmVersion: "cancun",
    },
  },
};
export default config;
```

Hardhat does NOT need `viaIR: true` — it handles stack depth on its own.

## tsconfig.json

```json
{
  "compilerOptions": {
    "target": "es2020",
    "module": "commonjs",
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "strict": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "outDir": "dist",
    "rootDir": "."
  },
  "include": ["./hardhat.config.ts", "./test/**/*", "./scripts/**/*", "./typechain-types/**/*"]
}
```

`rootDir: "."` is required — without it `tsc` infers `./test` and errors with TS5011 once typechain-types is generated.

## Test pattern

```typescript
import { expect } from "chai";
import { ethers, fhevm } from "hardhat";
import { FhevmType } from "@fhevm/hardhat-plugin";
import type { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";
import type { MyConfidentialToken } from "../typechain-types";

describe("MyConfidentialToken", function () {
  let token: MyConfidentialToken;
  let tokenAddress: string;
  let owner: SignerWithAddress, alice: SignerWithAddress;

  beforeEach(async function () {
    if (!fhevm.isMock) this.skip(); // tests only run on mock fhevm

    [owner, alice] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("MyConfidentialToken");
    token = (await Factory.deploy(owner.address, "Token", "TKN", "https://x")) as unknown as MyConfidentialToken;
    tokenAddress = await token.getAddress();
  });

  it("mints encrypted balance", async function () {
    const enc = await fhevm
      .createEncryptedInput(tokenAddress, owner.address)
      .add64(1000)
      .encrypt();

    await token.mint(alice.address, enc.handles[0], enc.inputProof);

    const handle = await token.confidentialBalanceOf(alice.address);
    const clear = await fhevm.userDecryptEuint(FhevmType.euint64, handle, tokenAddress, alice);
    expect(clear).to.equal(1000n);
  });
});
```

Plugin helpers:
- `fhevm.createEncryptedInput(contract, user).addXX(value).encrypt()` → `{ handles, inputProof }`
- `fhevm.userDecryptEuint(FhevmType.euintXX, handle, contract, signer)` → bigint
- `fhevm.isMock` — gate tests on mock-only behavior

## Gotchas specific to Hardhat

- **Overloaded ERC-7984 functions**: use the explicit signature to avoid "ambiguous function description":
  ```typescript
  token["confidentialTransfer(address,bytes32,bytes)"](to, handle, proof);
  ```
- **Compile errors after dep upgrades**: nuke `cache/`, `artifacts/`, `typechain-types/` and recompile.
