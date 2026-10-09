# Design, Cost, and Deployed Apps to Learn From

## Principles

- **Keep the critical path short.** Latency follows the longest chain of dependent FHE operations (see **zama-protocol** → `references/concepts.md`).
- **Avoid shared encrypted state.** One encrypted balance or total that every user touches links their transactions. Per-user or per-wallet state keeps them independent.
- **Pick cheap operations.** Shifts can replace multiplication and division by powers of two. Keep ranges and rounding correct.
- **Keep the economics intact.** Treat client-computed values as untrusted, and keep refunds, cancellation and settlement stages working after any optimization.

## Deployed examples

Read verified source on Etherscan. The first two rows are fixed deployments that the registry does not track. Look up the others by name in the registry (**zama-protocol** → `references/addresses.md`). For a proxy, read its current implementation and linked libraries.

| Pattern | Contract | Start with |
|---------|----------|------------|
| Sealed bids paid in ERC-7984 | [AuctionToken](https://etherscan.io/address/0x04a5b8C32f9c38092B008A4939f1F91D550C4345#code) | `submitEncryptedBid`, `_computeBidAllocation`: payment checks on transferred amounts, division by a public denominator |
| Per-user wallets created as clones | [WalletFactory](https://etherscan.io/address/0xBf58EE954CaeeF84B44F30131421e606272E393F#code) | `WalletFactory`, `AuctionWallet.initialize`: partitioned custody, configuring FHE in a clone |
| Swap with escrow and fees | Registry entry `CONFIDENTIAL_SWAP` (Ethereum) | `IntentLifecycleLib`, `EscrowLib`, `FeeLib.takeFee`: partitioned escrow, a fee computed with a shift, and why a shift of 64 needs its own case |
| Batched deposits with an aggregate reveal | Registry entries of type `vault_batcher` (Ethereum) | `VaultBatcherConfidential`, OpenZeppelin `BatcherConfidential`: `_join`, `dispatchBatchCallback`, `_claim`, proof checks and rounding. Small batches expose individual amounts |

Verified source is not an audit. Read the callers and callees of any function you adapt, and check the installed API before reusing code.
