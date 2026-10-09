# Planning a Confidential App

## Decide what must stay secret

List each value, who may read it, and what becomes public at the end. Use FHE when contracts must keep computing on a secret across transactions. A public computation needs no FHE, and proving a single fact once may suit a zero-knowledge proof better.

Reveal only what settlement needs. Values that are only paid out can move as encrypted transfers and never become public.

## Account for what still leaks

- Plaintext deposits and withdrawals show amounts at the edges of the system.
- Participant addresses, timing and call patterns link activity.
- An aggregate over a few users can expose each of them.

## Budget cost and latency

The host chain meters FHE work in HCU. Each transaction has a cap on total HCU and a separate cap on the depth of operations that depend on each other. The caps limit one transaction. They do not promise throughput. Count every FHE operation, including those inside token transfers, and the longest chain of dependent operations: that chain sets latency. Costs per operation are in the [HCU table](https://docs.zama.org/protocol/solidity-guides/development-guide/hcu). Mock gas says nothing about coprocessor latency. Measure on a real network.

## How the pieces fit

Host-chain contracts check permissions and record handles. Coprocessors compute ciphertexts off-chain. The Gateway coordinates requests, and the KMS decrypts with threshold cryptography only for authorized parties. Apps reach input verification and decryption through the SDK and its relayer. Details are in the [protocol litepaper](https://docs.zama.org/protocol/zama-protocol-litepaper).

Relayer access and billing are described in the [relayer API key guide](https://docs.zama.org/protocol/sdk/guides/relayer-api-keys.md). Host gas, protocol fees and hosted-service charges are separate costs.
