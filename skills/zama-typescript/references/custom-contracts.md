# SDK custom-contract flows

Use this note when the app interacts with a custom contract that stores FHE types directly, such as voting, auctions, identity, access control, games, or other non-token contracts.

Do not use the token helpers as the default answer for these cases.

## Browser and React path

For custom contracts in browser or React apps:

- use `useEncrypt` to produce encrypted handles and `inputProof`
- convert handles and proof to ABI-friendly hex values
- submit them to the contract call
- read the returned encrypted handles
- use `useUserDecrypt` to decrypt the final result

Typical pattern:

1. collect plaintext user input
2. call `useEncrypt`
3. send `handles` + `inputProof` to the contract
4. read the encrypted handle back from the contract
5. gate `useUserDecrypt` behind `useIsAllowed`

## Non-React path

For non-React TypeScript integrations:

- use the core SDK plus signer/relayer setup from `setups/`
- inspect the encrypt/decrypt guide and low-level contract builders
- keep the same rule: encrypt for the exact target contract, then decrypt only the output handles you need

## Rules that matter most

- The target `contractAddress` used during encryption must match the contract that consumes the input.
- `encrypt()` returns `Uint8Array` handles and proof; convert them with viem `bytesToHex` or ethers `hexlify` before passing them to contract calls.
- Gate decrypt operations behind the session-authorization checks instead of surprising the user with a wallet popup.
- Keep token guidance and custom-contract guidance separate. ERC-7984 helpers are not the generic answer here.

## Related

- `permissions.md`
- `react.md`
- `tokens.md`
