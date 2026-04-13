---
name: zama-react-sdk
description: React integration guide for `@zama-fhe/react-sdk`. Covers `ZamaProvider`, official hooks, wagmi/viem/ethers stack choice, explicit authorization UX, pending unshield recovery, and the frontend mistakes agents make when integrating the Zama React SDK.
---

# Zama React SDK

## What You Probably Got Wrong

**You wrote custom orchestration where official hooks already exist.** In React, the default should be the official hooks first, not raw SDK calls plus your own cache and state machine.

**You triggered signing on render.** `useAllow()` or decrypt flows must be gated behind explicit user action. Decrypt-on-render is bad UX and the wrong default.

**You put the SDK subtree inside `StrictMode`.** That causes avoidable lifecycle noise and remount problems. Keep the SDK subtree outside `<React.StrictMode>`.

**You mixed stack adapters.** If the app already uses wagmi, stay on the wagmi path. If it already uses viem clients, stay on viem. Do not mix wagmi, viem, and ethers patterns without a strong reason.

## When to Use

Use this skill when the target integration is a React or Next.js app built on `@zama-fhe/react-sdk`.

Typical cases:

- frontend confidential token integrations
- apps using wagmi, viem, or ethers
- migration from older frontend relayer or fhevm-style patterns

## Reference Repository

Resolve all repo-relative paths in this skill against:

`https://github.com/zama-ai/sdk/tree/prerelease`

If the public source of truth moves later, update this section first instead of rewriting the whole skill.

## Source Priority

1. `docs/gitbook/src/guides/configuration.md`
2. `docs/gitbook/src/guides/authentication.md`
3. `docs/gitbook/src/guides/nextjs-ssr.md`
4. `docs/gitbook/src/guides/check-balances.md`
5. `docs/gitbook/src/guides/handle-errors.md`
6. `docs/gitbook/src/reference/react/*.md`
7. Approved official React examples in the SDK repository:
   - `examples/react-wagmi/`
   - `examples/react-viem/`
   - `examples/react-ethers/`
8. API reports only if exported surface details are still unclear

## Reference Files

The following paths are relative to the Reference Repository above.

- `examples/react-wagmi/src/providers.tsx`
- `examples/react-wagmi/src/app/page.tsx`
- `examples/react-viem/src/providers.tsx`
- `examples/react-ethers/src/providers.tsx`
- `references/provider-setup.md`
- `references/hook-map.md`
- `references/credential-ux.md`
- `references/storage-and-pending-unshield.md`
- `references/frontend-gotchas.md`
- `references/migration-from-old-frontend-patterns.md`

## Working Method

1. Pick the closest approved example for the target stack.
2. Open `provider-setup.md` to choose the stack and configure `ZamaProvider`.
3. Wire official hooks before writing custom orchestration (see `hook-map.md`).
4. Open only the reference note needed for the current question.
5. Inspect internal SDK source only if docs, approved examples, and API reports still leave an exported-surface question unanswered.

## TanStack Query Rules

`@zama-fhe/react-sdk` is built on top of TanStack Query. Follow these rules:

- prefer official SDK hooks over custom `useQuery` / `useMutation` wrappers
- do not reimplement invalidation behavior that the SDK hooks already handle
- do not add manual polling or refresh loops unless an approved example requires it
- keep provider, signer, token, and hook inputs stable across renders
- treat wallet and account changes as explicit lifecycle boundaries
- use the approved React examples as the source of truth for query and mutation structure

## Golden Path

Choose the stack (see `provider-setup.md`): wagmi, viem, or ethers.

Then:

1. Start from the matching approved example.
2. Configure `ZamaProvider` in a client-side module.
3. Wire reads and writes with official hooks (see `hook-map.md`).
4. Add explicit credential UX (see `credential-ux.md`).
5. Add persistence and pending unshield recovery where needed (see `storage-and-pending-unshield.md`).
6. Follow the approved examples for cache and invalidation behavior.

For migration from older patterns, open `migration-from-old-frontend-patterns.md` first.

## Common Pitfalls

- Putting the SDK subtree inside `<React.StrictMode>`
- Triggering decrypt or sign flows on render
- Exposing relayer auth secrets in browser code
- Forgetting pending unshield recovery
- Unsafe amount parsing with `parseFloat` instead of `parseUnits`
- Missing Vite or browser isolation configuration
- Forgetting to remount or rebind signer state on wallet changes in custom providers

## Done When

- The app uses `ZamaProvider` correctly for the chosen stack.
- Main confidential token flows use official hooks or documented low-level APIs.
- Credential UX is explicit and user-driven.
- Storage and pending unshield recovery are handled correctly where needed.
- The resulting integration matches the docs and approved examples.
