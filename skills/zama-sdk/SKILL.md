---
name: zama-sdk
description: Backend and non-React integration guide for `@zama-fhe/sdk`. Covers relayer/runtime choice, signers, storage, confidential token flows, delegation, wrapper discovery, and the mistakes agents make when integrating the Zama SDK outside React.
---

# Zama SDK

## What You Probably Got Wrong

**You used the React SDK in a backend.** `@zama-fhe/react-sdk` is not the right entry point for a Node.js service, worker, cron job, or custom non-React runtime. Use `@zama-fhe/sdk`.

**You picked the wrong relayer.** Backend code should use `RelayerNode`. `RelayerCleartext` is only for approved local or Hoodi cleartext flows. If the target is a browser app, stop and use `zama-react-sdk`.

**You hardcoded wrapper addresses.** If registry lookup exists, use it. Guessing wrapper addresses creates silent integration failures.

**You scoped credentials incorrectly.** Sharing one storage instance across unrelated users or requests is a real bug. Backend integrations must make storage scope explicit.

## When to Use

Use this skill when the target integration uses `@zama-fhe/sdk` directly instead of `@zama-fhe/react-sdk`.

Typical cases:

- Node.js scripts and services
- backend workers and jobs
- custom signer integrations
- non-React apps
- migration from older `relayer-sdk` or fhevm-style integration code

If the target is a React app, use `zama-react-sdk` instead.

## Reference Repository

Resolve all repo-relative paths in this skill against:

`https://github.com/zama-ai/sdk/tree/prerelease`

If the public source of truth moves later, update this section first instead of rewriting the whole skill.

## Source Priority

1. `docs/gitbook/src/guides/configuration.md`
2. `docs/gitbook/src/guides/authentication.md`
3. `docs/gitbook/src/guides/node-js-backend.md`
4. `docs/gitbook/src/guides/local-development.md`
5. `docs/gitbook/src/guides/shield-tokens.md`
6. `docs/gitbook/src/guides/transfer-privately.md`
7. `docs/gitbook/src/guides/unshield-tokens.md`
8. `docs/gitbook/src/guides/check-balances.md`
9. `docs/gitbook/src/reference/sdk/*.md`
10. Approved official examples in the SDK repository:
   - `examples/node-viem/`
   - `examples/node-ethers/`
   - `examples/example-hoodi/`
11. API reports only if exported surface details are still unclear

## Reference Files

The following paths are relative to the Reference Repository above.

- `examples/node-viem/src/index.ts`
- `examples/node-ethers/src/index.ts`
- `examples/example-hoodi/README.md`
- `examples/example-hoodi/WALKTHROUGH.md`
- `references/setup-and-subpaths.md`
- `references/core-operations.md`
- `references/delegation-and-credentials.md`
- `references/wrapper-discovery-and-gotchas.md`
- `references/migration-from-old-sdk-patterns.md`

## Working Method

1. Pick the closest approved example.
2. Open `setup-and-subpaths.md` to choose relayer, signer, and storage.
3. Open only the reference note needed for the current question.
4. Inspect internal SDK source only if docs, approved examples, and API reports still leave an exported-surface question unanswered.

## Golden Path

Choose the runtime:

- backend, worker, cron, script → `RelayerNode`
- local cleartext or Hoodi cleartext demo → `RelayerCleartext`
- browser app → stop, use `zama-react-sdk` instead

Then:

1. Choose the signer: `ViemSigner`, `EthersSigner`, or `GenericSigner` only if required.
2. Choose storage: `memoryStorage` for scripts, `asyncLocalStorage` for concurrent servers.
3. Create `ZamaSDK`.
4. Discover or resolve the wrapper (see `wrapper-discovery-and-gotchas.md`).
5. Run the token flow (see `core-operations.md`): `shield()` → `confidentialTransfer()` → `balanceOf()` → `unshield()`.
6. Add credentials and delegation only when the product flow needs them (see `delegation-and-credentials.md`).

For migration from older patterns, open `migration-from-old-sdk-patterns.md` first.

## Common Pitfalls

- Using browser relayer patterns in a backend runtime
- Hardcoding wrapper assumptions without registry validation
- Reusing credential state across concurrent users
- Sharing one storage instance across unrelated users
- Stripping typed-data domain fields
- Forgetting to terminate `RelayerNode` in long-running processes or tests
- Mixing cleartext assumptions into production paths

## Done When

- The integration uses the current `@zama-fhe/sdk` APIs correctly.
- The chosen relayer, signer, and storage match the runtime.
- Shield, transfer, decrypt, and unshield flows follow docs-backed patterns.
- Credentials and delegation are implemented only where needed.
- No unsupported old SDK patterns remain.
