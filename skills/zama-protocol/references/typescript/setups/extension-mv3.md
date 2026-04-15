# MV3 browser extension setup

**Canonical doc:** `https://github.com/zama-ai/sdk/tree/main/docs/gitbook/src/guides/web-extensions.md`

The problem: MV3 service workers can be terminated after 30s idle. In-memory session state (wallet signature) is lost, forcing a re-sign on every interaction. Fix: pass **`chromeSessionStorage` as `sessionStorage`** (not as `storage`) — `chrome.storage.session` survives worker restarts.

```ts
import { ZamaSDK, RelayerWeb, SepoliaConfig, indexedDBStorage, chromeSessionStorage } from "@zama-fhe/sdk";
import { ViemSigner } from "@zama-fhe/sdk/viem";

const sdk = new ZamaSDK({
  relayer: new RelayerWeb({
    getChainId: () => signer.getChainId(),
    // Sepolia: spread SepoliaConfig as-is. Only override relayerUrl on mainnet.
    transports: { [SepoliaConfig.chainId]: { ...SepoliaConfig, network: RPC } },
  }),
  signer,
  storage: indexedDBStorage,          // encrypted FHE keypair — persistent
  sessionStorage: chromeSessionStorage, // wallet signature — survives worker restart
});
```

`manifest.json` needs `"permissions": ["storage"]`. Popup, background, and content scripts all share `chrome.storage.session` — sign once in the popup, background decrypts without another prompt. Browser close purges the session signature (indexedDB keypair survives).
