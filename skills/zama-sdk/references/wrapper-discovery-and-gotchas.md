# Wrapper Discovery and Gotchas

## Wrapper Discovery

Prefer official registry-driven flows:

- `discoverWrapper()` when starting from the plain ERC-20
- `underlyingToken()` when reverse-resolving the plain token

Do not hardcode wrapper assumptions unless the integration intentionally pins addresses.

## Important Gotchas

- preserve `EIP712Domain`
- keep `chainId` explicit
- handle `FHE_GAS_LIMIT` correctly for FHE operations
- respect the 10-contract credential limit
- keep `sessionTTL` at or below one year
- do not use cleartext mode on Mainnet or Sepolia
- keep credential storage scoped to the current user or request
- terminate `RelayerNode` on shutdown in scripts, workers, and tests

## Network Notes

Use the official presets for supported networks, especially Sepolia and Hoodi-related flows.
