# Storage and Pending Unshield

## Storage

Use `indexedDBStorage` for browser persistence.

Keep credential storage and any session-specific storage aligned with the approved examples.

## Pending Unshield Recovery

Use:

- `savePendingUnshield`
- `loadPendingUnshield`
- `clearPendingUnshield`
- `useResumeUnshield`

Use this when the app must recover an unwrap/finalize flow after a reload or interruption.

## Minimal Shape

```tsx
const sdk = useZamaSDK();
const { mutateAsync: resumeUnshield } = useResumeUnshield({ tokenAddress });

useEffect(() => {
  async function recover() {
    const pending = await loadPendingUnshield(sdk.storage, tokenAddress);
    if (!pending) return;
    try {
      await resumeUnshield({ unwrapTxHash: pending });
      await clearPendingUnshield(sdk.storage, tokenAddress);
    } catch (err) {
      console.error("Failed to resume unshield:", err);
    }
  }

  void recover();
}, [resumeUnshield, sdk.storage, tokenAddress]);
```
