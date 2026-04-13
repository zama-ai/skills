# Provider Setup

## Provider Rules

- keep `ZamaProvider` in client-only code
- do not put the SDK subtree inside `<React.StrictMode>`
- pass relayer, signer, and storage explicitly
- use the stack-specific subpath when needed

## Stack Choices

- `@zama-fhe/react-sdk/wagmi`
- `@zama-fhe/react-sdk/viem`
- `@zama-fhe/react-sdk/ethers`
- Choose the stack that already owns wallet state in the app.
- Do not mix multiple stack adapters in one integration unless the app already depends on them.

## Example Shape

```tsx
<QueryClientProvider client={queryClient}>
  <ZamaProvider relayer={relayer} signer={signer} storage={indexedDBStorage}>
    {children}
  </ZamaProvider>
</QueryClientProvider>
```
