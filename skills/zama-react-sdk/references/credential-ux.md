# Credential UX

## Preferred Flow

1. read `useIsAllowed`
2. if false, show an explicit action
3. trigger `useAllow`
4. run the confidential read or decrypt flow

## Why

- avoids blind signing on render
- keeps wallet prompts understandable
- matches the recommended balance decryption UX

## Session Cleanup

Use:

- `useRevoke` for specific contracts
- `useRevokeSession` for full session cleanup

## Minimal Shape

```tsx
const { data: allowed } = useIsAllowed();
const { mutateAsync: allow } = useAllow();

if (!allowed) {
  return <button onClick={() => allow([tokenAddress])}>Authorize wallet</button>;
}
```
