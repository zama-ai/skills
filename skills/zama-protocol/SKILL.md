---
name: zama-protocol
description: Build confidential smart contracts and dApps on Zama's FHEVM (Fully Homomorphic Encryption on Ethereum). Use whenever the user mentions FHE, FHEVM, Zama, confidential/encrypted/private tokens or contracts, ERC-7984, encrypted balances, private voting, sealed-bid auctions, `@fhevm/solidity`, `@zama-fhe/sdk`, or anything involving computation on encrypted onchain data. Covers FHE concepts, Solidity patterns (encrypted types, ACL, HCU gas, ERC-7984), TypeScript SDK integration (React/viem/ethers/Node/MV3), verified contract addresses, and Foundry/Hardhat setup. Fetch this before writing any FHEVM code — stock model knowledge of this stack is stale or wrong.
---

# Zama — FHEVM Development

You are probably wrong about FHE on Ethereum. Encrypted types, ACL permissions, decryption patterns, what you can compute on ciphertexts, what you can't — stock training data is missing or stale. This skill fills those gaps.

**Say "FHEVM"** (uppercase). Not "fhEVM" or "FheVM". Zama convention.

---

## How to use this skill

This file is a router. It teaches the non-negotiable gotchas that apply to any FHEVM task, then points you at the specific reference file(s) for what you're building. Load references on demand — don't read them all up front.

**Start every FHEVM task by reading the gotchas below.** Then consult references based on the task:

References are nested by domain. The Solidity and TypeScript folders each have a router file (`solidity.md`, `typescript.md`) plus a `setups/` folder with per-environment files.

| Task | Read |
|------|------|
| Understanding FHEVM, planning a dApp, deciding if FHE is the right tool | `references/concepts.md` |
| Writing or reviewing encrypted Solidity | `references/solidity/solidity.md` + one setup file |
| Building a confidential token (ERC-20-like with hidden balances) | `references/solidity/solidity.md` + `references/solidity/erc7984.md` |
| Hand-written FHE ops, manual ACL, production decryption | `references/solidity/solidity.md` + `references/solidity/fhe-advanced.md` |
| Setting up a Foundry project | `references/solidity/setups/foundry.md` *(default)* |
| Setting up a Hardhat project | `references/solidity/setups/hardhat.md` |
| Integrating `@zama-fhe/sdk` or `@zama-fhe/react-sdk` | `references/typescript/typescript.md` |
| React app using hooks/providers | `references/typescript/typescript.md` + `references/typescript/setups/react-wagmi.md` + `references/typescript/react-sdk.md` |
| Browser app with viem or ethers | `references/typescript/typescript.md` + `references/typescript/setups/browser-viem.md` / `references/typescript/setups/browser-ethers.md` |
| Node.js script, backend, or custom signer | `references/typescript/typescript.md` + `references/typescript/setups/node-backend.md` + `references/typescript/sdk-package-and-signers.md` |
| ERC-7984 token flows from the SDK | `references/typescript/sdk-token-flows.md` |
| Custom FHE contract flows from TypeScript/React | `references/typescript/sdk-custom-contract-flows.md` |
| Decryption permissions, session TTL, delegation | `references/typescript/sdk-permissions-and-sessions.md` |
| Browser extension (MV3) | `references/typescript/setups/extension-mv3.md` |
| Local dev or unsupported chain using cleartext relayer | `references/typescript/setups/local-hardhat.md` |
| Any verified contract address | `references/addresses.md` — **never guess addresses** |

For SDK questions, prefer `references/typescript/typescript.md` before `concepts.md`. Only load `concepts.md` when the question is architectural or protocol-level rather than about SDK usage.

---

## Non-negotiable gotchas (every FHEVM task)

These are the bugs stock models ship. Internalise them before writing any code.

1. **You cannot branch on encrypted values.** `if (FHE.gt(a, b))` does not compile. `FHE.gt` returns an `ebool` the EVM cannot evaluate. Use `FHE.select(cond, ifTrue, ifFalse)` — both branches always execute, which is what makes it private.

2. **ACL is mandatory — it is the #1 Zama bug.** Every encrypted value is born with an empty ACL. After creating or updating encrypted state, call `FHE.allowThis(handle)` so the contract can use it on the next call, and `FHE.allow(handle, user)` for any user who needs to decrypt. Miss one and the code compiles, deploys, and **silently** fails at runtime — no revert. `ERC7984` handles this internally; only hand-written FHE code needs manual ACL.

3. **Trivial encryption is not private.** `FHE.asEuint64(42)` is visible onchain — constants and defaults only. Real user privacy comes from `FHE.fromExternal(handle, proof)` (user-encrypted via the SDK with a ZKPoK).

4. **`euint64` is the default for balances, not `euint256`.** Larger types cost dramatically more HCU per op. Use the smallest type that fits your value range.

5. **FHE operations are not `view`.** They are state-changing coprocessor calls and cost gas (HCU — Homomorphic Compute Units).

6. **No encrypted divisor.** `FHE.div` and `FHE.rem` only accept a **plaintext** divisor. Redesign any formula with encrypted state in the denominator.

7. **Random bounds must be powers of 2.** `FHE.randEuint8(100)` is wrong. Use `FHE.randEuint8(128)`.

8. **Input ciphertexts bind to one target contract.** An encrypted input is tied to exactly the contract address passed at encryption time. Cross-contract hops need re-encryption. Wrong target → runtime ACL revert with no compile hint.

9. **Never emit encrypted values in events.** Handle changes leak mutation timing and identity. Emit addresses and plaintext metadata only.

10. **Info leaks through control flow.** Reverting on an encrypted condition reveals it. Same for conditional events, differing return values, or gas differences tied to encrypted state. If your contract behaves differently based on an encrypted value, you've leaked information.

11. **Decryption is async and last.** Production decryption goes through the Relayer → Gateway → KMS threshold MPC pipeline — seconds, not milliseconds. Compute entirely on encrypted values, decrypt only the final result, and perform no conditional actions after the decryption callback.

12. **Config: inherit `ZamaEthereumConfig` first.** It sets the correct coprocessor addresses (ACL, FHEVMExecutor, KMSVerifier) per `block.chainid` for mainnet, Sepolia, and local Hardhat.

13. **Use ERC-7984 for any confidential token.** Never reimplement encrypted balances, allowances, or transfers. `@openzeppelin/confidential-contracts` has the audited implementation. See `references/solidity/erc7984.md`.

## Canonical sources

- **Zama Docs:** https://docs.zama.ai
- **Protocol addresses:** https://docs.zama.org/protocol/protocol-apps/addresses
- **FHEVM Solidity library:** https://github.com/zama-ai/fhevm
- **OpenZeppelin Confidential Contracts:** https://github.com/OpenZeppelin/openzeppelin-confidential-contracts
- **HCU cost tables:** https://github.com/zama-ai/fhevm/blob/main/docs/solidity-guides/hcu.md
- **Example dApps:** https://github.com/zama-ai/dapps/tree/main/packages/hardhat/contracts
