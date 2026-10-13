# Design, Cost, and Deployed Apps to Learn From

## Principles

- **Keep the critical path short.** Latency follows the longest chain of dependent FHE operations (see **zama-protocol** → `references/concepts.md`).
- **Avoid shared encrypted state.** One encrypted balance or total that every user touches links their transactions. Per-user or per-wallet state keeps them independent.
- **Pick cheap operations.** Shifts can replace multiplication and division by powers of two. Keep ranges and rounding correct.
- **Keep the economics intact.** Treat client-computed values as untrusted, and keep refunds, cancellation and settlement stages working after any optimization.

## Deployed examples

Links open Etherscan-verified source. For a proxy, open the implementation from the proxy's code tab: it can change on upgrade. Each row gives the contract's [registry](https://github.com/zama-ai/protocol-registry) key where it has one, and the registry decides which deployment is current (**zama-protocol** → `references/addresses.md`). It also lists further wrappers and batchers by type.

| Pattern | Contract | Start with |
|---------|----------|------------|
| ERC-7984 wrapper of an ERC-20 | [cUSDC](https://etherscan.io/address/0xe978F22157048E5DB8E5d07971376e86671672B2#code) (`CONFIDENTIAL_USDC`), proxy to `ConfidentialWrapper` | `wrap`, `unwrap` (marks the amount publicly decryptable), `finalizeUnwrap` (deletes the request, checks the proof, then pays). This is Zama's upgradeable variant with a blocklist; build new tokens on OpenZeppelin's `ERC7984ERC20Wrapper` |
| Finding a token's wrapper on-chain | [ConfidentialTokenWrappersRegistry](https://etherscan.io/address/0xeb5015fF021DB115aCe010f23F55C2591059bBA0#code) (`TOKEN_WRAPPER_REGISTRY`), proxy | `getConfidentialTokenAddress`, `isConfidentialTokenValid`: look wrappers up instead of hard-coding them |
| Batched deposits with an aggregate reveal | [Deposit](https://etherscan.io/address/0xA07c00A3b955B805B3Ea76b086f95a3e793715D5#code) and [redeem](https://etherscan.io/address/0x3a906d6509EB4171Ee9fC71D083fb1638BaF083D#code) batchers (`STEAKHOUSE_CONFIDENTIAL_PRIME_USDC_DEPOSIT_VAULT_BATCHER`, `…_REDEEM_VAULT_BATCHER`) | `VaultBatcherConfidential.join`, OpenZeppelin `BatcherConfidential`: `_join`, `dispatchBatchCallback`, `_claim`, `recover`, rounding, slippage. Small batches expose individual amounts |
| Receiver callback that checks the token | [VaultBatcherConfidentialRouter](https://etherscan.io/address/0x11c6Acfd368DDFAB97d15649eB8043C0197fac4C#code) (`VAULT_BATCHER_ROUTER`) | `onConfidentialTransferReceived` accepts only tokens listed in the wrapper registry; copy that check. Do not copy its direct executor call: use the `amount` the callback receives, and take other encrypted inputs in a direct call with `FHE.fromExternal` |
| Swap with escrow and fees | [ConfidentialSwap](https://etherscan.io/address/0x8Fe22dC7e624c02b1805d41E09741490E1018C01#code) (`CONFIDENTIAL_SWAP`), proxy | `IntentLifecycleLib`, `EscrowLib`, `FeeLib.takeFee`: partitioned escrow, a fee computed with a shift, and why a shift of 64 needs its own case |
| Sealed bids paid in ERC-7984 | [AuctionToken](https://etherscan.io/address/0x04a5b8C32f9c38092B008A4939f1F91D550C4345#code) | `submitEncryptedBid`, `_computeBidAllocation`: payment checks on transferred amounts, division by a public denominator |
| Per-user wallets created as clones | [WalletFactory](https://etherscan.io/address/0xBf58EE954CaeeF84B44F30131421e606272E393F#code) | `WalletFactory`, `AuctionWallet.initialize`: partitioned custody, configuring FHE in a clone |

The swap and the auction grant decryption access to a compliance address. Those grants belong to those apps; do not copy them.

Verified source is not an audit. Read the callers and callees of any function you adapt, and check the installed API before reusing code.
