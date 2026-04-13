# Frontend Gotchas

## Main Rules

- do not use `<React.StrictMode>` around the SDK subtree
- keep SDK setup in client components only
- never expose relayer auth secrets in browser code
- use precision-safe parsing such as `parseUnits`, not `parseFloat`
- follow wallet/account reactivity patterns from the approved examples
- check `useIsAllowed()` before prompting for signatures
- do not trigger `useAllow()` or decrypt flows from render or mount

## Environment Notes

- configure Vite `optimizeDeps.exclude` when required
- respect COOP/COEP requirements where applicable
- keep SSR boundaries explicit in Next.js
