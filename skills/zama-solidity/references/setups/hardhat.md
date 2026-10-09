# Hardhat

Use Hardhat 3 with `@fhevm/hardhat-plugin-v3`. Its source, README and example project live in [fhevm-mocks](https://github.com/zama-ai/fhevm-mocks) under `hardhat/v3/`. Use the `release/*` branch that matches the protocol version you target. Copy dependency versions from the example project's `package.json`, and register the plugin in `plugins` in `hardhat.config.ts`.

When peer dependency ranges conflict (for example, the OpenZeppelin confidential contracts pinning a different `@fhevm/solidity`), add an explicit override instead of installing with `--legacy-peer-deps`, which also skips Hardhat's own peer packages:

```json
"overrides": {
  "@openzeppelin/confidential-contracts": { "@fhevm/solidity": "$@fhevm/solidity" }
}
```

Then compile and run the tests. Passing mock tests do not prove the combination is supported on a live network. Check the release notes.

The plugin provides helpers to encrypt test inputs and decrypt results, including `decryptPublic*WithSignatures` for testing reveals. Test the zero-transfer path, access in later transactions, and replayed or forged reveals.

`@fhevm/hardhat-plugin` for Hardhat 2 is the legacy path.
