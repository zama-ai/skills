---
name: zama-typescript
description: Build, review, or debug Zama FHEVM TypeScript/JavaScript integration — @zama-fhe/sdk, @zama-fhe/react-sdk, encryption/decryption, ERC-7984 tokens, permits/operators, wagmi/viem/ethers, browser or Node services, and async wallet/transaction flows. Load zama-protocol first; use zama-solidity for contracts.
license: BSD-3-Clause-Clear
---

# Zama TypeScript

Load **zama-protocol** first. Use `references/patterns.md` for integration pitfalls and the matching public docs below for exact signatures; do not copy whole SDK tutorials into this skill.

## Select the package and release

Use `@zama-fhe/sdk` for core integration and `@zama-fhe/react-sdk` for React; respect their peer dependencies. `@fhevm/sdk` is a published low-level backend. The high-level SDK pins its compatible backend: do not independently replace it with npm `latest`.

`@zama-fhe/relayer-sdk` is deprecated. The [protocol changelog](https://docs.zama.org/protocol/changelog) records security-only maintenance until 2026-11-06, then no support. Use it only while maintaining/migrating existing integrations or compatible pinned tooling.

Check the project's installed package declarations and release channel before using a documented feature. Hosted docs and repository `main` may describe a newer release than the project uses.

## Route by task

| Task | Public source |
|------|---------------|
| Setup, signer/provider, transports/storage | [Quick start](https://docs.zama.org/protocol/sdk/getting-started/quick-start.md), [configuration](https://docs.zama.org/protocol/sdk/guides/configuration.md) |
| Tokens, wrappers, shield/unshield | [Core SDK API](https://docs.zama.org/protocol/sdk/api-references/sdk.md) |
| React/wagmi hooks and query behavior | [React API](https://docs.zama.org/protocol/sdk/api-references/react.md) |
| Custom contracts: encrypted inputs and outputs | [Encrypt/decrypt guide](https://docs.zama.org/protocol/sdk/guides/encrypt-decrypt.md) |
| Permits, decryption delegation, credential storage | [Permit model](https://docs.zama.org/protocol/sdk/concepts/permit-model.md), [delegated decryption](https://docs.zama.org/protocol/sdk/guides/delegated-decryption.md) |
| Node request identity/storage | [Node guide](https://docs.zama.org/protocol/sdk/guides/node-js-backend.md) |
| Browser/WASM compatibility | [Supported environments](https://docs.zama.org/protocol/sdk/getting-started/supported-environments.md), [security headers](https://docs.zama.org/protocol/sdk/concepts/security-model.md#browser-security-headers) |
| Verified deployment addresses | **zama-protocol** → `references/addresses.md` |

For other tasks, discover the appropriate stable documentation through the public [SDK index](https://raw.githubusercontent.com/zama-ai/sdk/main/llms.txt). Avoid `/beta/` documentation unless the project uses that release channel. Private app code, repository links and unreleased implementation details must not enter distributed advice.
