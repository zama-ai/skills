# Zama Solidity — Confidential Contracts

This reference covers config and the FHE gotchas that apply to every contract. Pair it with:

- **One setup file**: `setups/foundry.md` (default) or `setups/hardhat.md`
- `erc7984.md` — if the user wants a confidential token (encrypted ERC20, private-balance token, FHE token). Mint/burn recipe, full ERC-7984 interface, extensions.
- `fhe-advanced.md` — only if going beyond `ERC7984`'s built-ins: hand-written FHE arithmetic/comparisons, manual ACL, production decryption, raw encrypted types.

## Configuration

**Always inherit `ZamaEthereumConfig`** — it sets the correct FHE coprocessor addresses (ACL, FHEVMExecutor, KMSVerifier) per `block.chainid`. Supported: Ethereum mainnet, Sepolia, local Hardhat (31337).

## Confidential Tokens

For any confidential token (encrypted ERC20, private-balance token, FHE token), use **ERC-7984** from OpenZeppelin's confidential contracts library. Recipe, interface, and extensions in `erc7984.md`. Never reimplement encrypted balances, allowances, or transfers.

## Gotchas (read before writing any FHE code)

- **Setup**: inherit `ZamaEthereumConfig` (otherwise FHE op calls go to `address(0)` and revert with no reason). For build config, start from the official templates (`fhevm-foundry-template`, `fhevm-hardhat-template`) and don't enable `via_ir` / `viaIR` preemptively — it's a `solc` feature you turn on only when `solc` actually reports "stack too deep."
- **Default type**: `euint64` for balances. `euint256` is dramatically more expensive per op.
- **Confidentiality**: `FHE.fromExternal()` is real encryption. `FHE.asEuintX(plaintext)` is **visible onchain** — constants only.
- **No `view`**: FHE ops are state-changing (coprocessor calls).
- **Control flow**: `ebool` cannot go in `if`/`require`/`while`. Use `FHE.select(cond, ifTrue, ifFalse)` — both branches must be encrypted values (materialise `FHE.asEuint64(0)`, not a literal), and both branches always execute (rejected paths still pay for their transfers/ops).
- **No encrypted divisor**: `FHE.div`/`FHE.rem` only accept a **plaintext** divisor. Redesign any formula with encrypted state in the divisor.
- **ACL (#1 bug)**: call `FHE.allowThis()` after creating/computing encrypted values, or the next call that reads the stored handle reverts with `ACLNotAllowed`. The failure is **deferred** — the deploy and first interaction succeed, the bug shows up on the second call. `ERC7984` handles this internally; only hand-written FHE code needs it. For single-tx cross-contract handles prefer `FHE.allowTransient` over persistent `FHE.allow`.
- **Input ciphertexts bind to one target contract**: `encryptUint64(value, user, target)` ties the proof to exactly `target`. Every hop needs its own encryption. Wrong target → runtime ACL revert with no compile hint.
- **Events**: never emit encrypted values — handle changes leak mutation timing. Emit addresses only.
- **Silent failures**: on insufficient balance FHE contracts transfer 0 via `FHE.select` — no revert. Test the zero-transfer case and call every function twice to prove ACL.
- **Public decrypt must be re-marked**: after every update to a publicly-decryptable state var, re-call `FHE.makePubliclyDecryptable(handle)`.
- **Decryption**: async Gateway in production; `decrypt`, `userDecrypt`, etc. are test-only helpers and don't exist on production `FHE.sol`. Make decryption the last step — no conditional actions after.
- **Info leaks**: reverting on an encrypted condition reveals it. Same for conditional events, differing return values, or gas differences tied to encrypted state.
- **Overloaded ERC-7984 functions**: call with explicit signature, e.g. `token["confidentialTransfer(address,bytes32,bytes)"](...)`.
- **HCU limits**: per-tx 20M (`maxHCUPerTx`), per-tx sequential depth 5M (`maxHCUDepthPerTx`), per-block `uint48.max` (`hcuPerBlock` — effectively unbounded today, so the per-tx caps are the binding constraint). Prefer scalar operands, smallest type that fits, split functions over 10M. Full tables: https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md
- **Standard Solidity still applies**: CEI + `nonReentrant`, SafeERC20, access control, no hardcoded `1e18` (ERC-7984 uses **6** decimals), Sepolia before mainnet.

## Sources

- **HCU costs:** https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md
- **Zama Docs:** https://docs.zama.org
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
- **Zama dApps (examples):** https://github.com/zama-ai/dapps/tree/main/packages/hardhat/contracts
- **Protocol Apps (deployed):** https://github.com/zama-ai/protocol-apps/tree/main/contracts
