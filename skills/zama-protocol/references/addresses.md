# Deployed Contracts

The public [protocol registry](https://github.com/zama-ai/protocol-registry) is the source of truth for Zama protocol and app addresses on mainnet and testnet. The docs [address page](https://docs.zama.org/protocol/protocol-apps/addresses) shows the same data for people.

Read `https://raw.githubusercontent.com/zama-ai/protocol-registry/main/mainnet.json` (or `testnet.json`). `chains` gives each chain's ID and block explorer. Each entry in `contracts` has an `address`, a `chain` and a `type`, such as `fhevm_acl`, `confidential_wrapper` or `token_wrapper_registry`.

Never invent or recall an address. Take it from the registry, then check the code on the chain's explorer. For a proxy, check its current implementation.

- **Contracts do not hard-code FHEVM addresses.** They inherit the config contract for their chain, such as `ZamaEthereumConfig` (see **zama-solidity**).
- **Wrappers are separate tokens.** An ERC-7984 wrapper and its underlying ERC-20 have different addresses.
- **A chain preset is not a deployment.** An SDK or library preset for a chain does not prove the protocol runs there. The registry and the [changelog](https://docs.zama.org/protocol/changelog) do.
