---
name: zama-protocol
description: Explain or plan Zama FHEVM applications, protocol architecture, encrypted state, ACL, handles, HCU, decryption, or deployment selection. Load first for Zama encrypted Solidity or TypeScript work; use zama-solidity for contracts and zama-typescript for SDK integration.
license: BSD-3-Clause-Clear
---

# Zama Protocol

Load the companion skill for implementation. Read `references/concepts.md` for architecture/privacy planning and `references/addresses.md` for deployment discovery; load only what the task needs.

## Universal corrections

- **FHE computations are symbolic onchain.** Contracts return ciphertext handles; coprocessors compute asynchronously. A successful receipt does not establish ciphertext readiness.
- **Handles are identifiers.** Different handles can encrypt equal values. Use FHE comparisons for secrets; never infer plaintext from handle bytes or reuse handles across chains.
- **Keep permissions with the value.** Persist contract access with `FHE.allowThis` for stored results; grant users access only when intended. Transient grants expire after the transaction. Imported inputs do not grant persistent access automatically.
- **Import at the proof's target.** Input proofs bind to a contract and sender. After `FHE.fromExternal`, forward handles with ACL permission; each contract hop does not require re-encryption. When accepting existing handles, verify caller permission as well as contract access.
- **Encrypted conditions cannot control Solidity branching.** Use `FHE.select`; both arms are computed. Reverts/events tied to revealed secrets change privacy.
- **Trivial encryption exposes its input.** `FHE.asEuintN(plaintext)` does not make a public amount private. Prefer client-encrypted inputs for secrets.
- **Check type support and costs.** ERC-7984 balances are `euint64`; wider types have different operation sets. `div`/`rem` need plaintext divisors; bounded randomness needs a power-of-two bound.
- **Decryption is asynchronous.** Keep intermediates encrypted. Public settlement must verify proofs against expected frozen handles and prevent replay. User decryption requires the relevant contract/user ACL permissions; a signed permit alone does not grant them.
- **Metadata remains public.** Standard ERC-7984 events include handles. Addresses, timing, public deposits/withdrawals and reveal granularity can expose information without exposing ciphertext plaintexts directly.
- **Configure each FHE-calling contract.** Use the installed library's chain-appropriate config. Proxy/clone storage needs explicit configuration in its protected initialiser.

## Sources and version discipline

Use the [protocol changelog](https://docs.zama.org/protocol/changelog) and current deployment docs for live status. Public repository `main`, npm `latest`, and the deployed protocol can differ. Contract `getVersion()` numbers also differ from protocol release tags. Verify the project's installed versions and peer dependencies before selecting APIs; do not copy release-specific event/handle/relayer schemas from memory.

Read public [Solidity docs](https://docs.zama.org/protocol/solidity-guides) or [SDK docs](https://docs.zama.org/protocol/sdk) for the task. Private app code and links must never enter distributed skills; the Solidity code map contains Etherscan-verified mainnet examples.
