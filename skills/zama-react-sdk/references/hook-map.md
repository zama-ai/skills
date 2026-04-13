# Hook Map

## Main Hooks

- balances: `useConfidentialBalance`, `useConfidentialBalances`
- writes: `useShield`, `useConfidentialTransfer`, `useUnshield`
- token helpers: `useToken`, `useReadonlyToken`
- recovery: `useResumeUnshield`
- credentials: `useAllow`, `useRevoke`, `useRevokeSession`, `useIsAllowed`
- delegation: `useDelegateDecryption`, `useRevokeDelegation`, `useDelegationStatus`, `useDecryptBalanceAs`, `useBatchDecryptBalancesAs`

## Rule

Use the highest-level official hook that already matches the product flow.
