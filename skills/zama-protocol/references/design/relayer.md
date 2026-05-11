# FHEVM: Relayer

The Relayer is the **only public HTTP endpoint** in the protocol. Users and dApps never send transactions to the gateway directly — they call the Relayer, which validates, submits the gateway transaction, listens for the response event, and stores the result for polling.

Three operations are exposed:
1. Input proof submission
2. Public decryption
3. User decryption (and delegated user decryption)

## API endpoints

All endpoints are versioned under `/v2/`. POST returns a job ID; GET polls. Responses share an envelope:

```json
{
  "status": "queued" | "succeeded" | "failed",
  "requestId": "<uuid>",
  "result": { /* per-endpoint */ } | null,
  "error": { "label": "...", "message": "...", "details": [] } | null
}
```

`"succeeded"` (not `"completed"`) is the terminal success status. Pending requests respond `202` with a `Retry-After` header.

### Input proof

```text
POST /v2/input-proof
GET  /v2/input-proof/{job_id}
```

Request:

```json
{
  "contractChainId": "<chain_id>",
  "contractAddress": "0x...",
  "userAddress":     "0x...",
  "ciphertextWithInputVerification": "<hex without 0x>",
  "extraData":       "00"
}
```

`ciphertextWithInputVerification` is the ABI-encoded `(ciphertext, zkproof)` blob.

Success result:

```json
{ "accepted": true, "handles": ["0x..."], "signatures": ["0x..."] }
```

`accepted: false` is `status: "succeeded"`, not an error — the proof was processed and rejected by coprocessor consensus.

### Public decryption

```text
POST /v2/public-decrypt
GET  /v2/public-decrypt/{job_id}
```

```json
{
  "ciphertextHandles": ["0x..."],
  "extraData":         "00"
}
```

The host chain is inferred from the handles' embedded chain ID — there is **no** `contractChainId` field in this endpoint. All handles must be marked publicly decryptable in the host ACL (validated before queuing).

Result:

```json
{
  "decryptedValue": "<abi-encoded values>",
  "signatures":     ["0x..."],
  "extraData":      "00"
}
```

### User decryption

```text
POST /v2/user-decrypt
GET  /v2/user-decrypt/{job_id}
```

```json
{
  "handleContractPairs": [{ "handle": "0x...", "contractAddress": "0x..." }],
  "requestValidity":     { "startTimestamp": 1700000000, "durationDays": 1 },
  "contractsChainId":    "<chain_id>",
  "contractAddresses":   ["0x..."],
  "userAddress":         "0x...",
  "signature":           "<130-hex EIP-712, no 0x>",
  "publicKey":           "<transport public key hex>",
  "extraData":           "00"
}
```

`signature` is the user's EIP-712 signature over `UserDecryptRequestVerification`, generated client-side with the user's Ethereum private key.

Result:

```json
{
  "result": [
    { "payload": "<signcrypted share hex>", "signature": "0x...", "extraData": "00" }
  ]
}
```

The shares are returned as an **array of objects** (one per KMS node), not as parallel arrays. The user combines shares client-side; see [./flow-user-decryption.md](./flow-user-decryption.md).

### Delegated user decryption

```text
POST /v2/delegated-user-decrypt
GET  /v2/delegated-user-decrypt/{job_id}
```

Body shape differs from user decryption — `requestValidity` is flattened to top-level fields, and the delegator/delegate replace `userAddress`:

```json
{
  "handleContractPairs": [{ "handle": "0x...", "contractAddress": "0x..." }],
  "startTimestamp":      "1700000000",
  "durationDays":        "1",
  "contractsChainId":    "<chain_id>",
  "contractAddresses":   ["0x..."],
  "delegatorAddress":    "0x...",
  "delegateAddress":     "0x...",
  "publicKey":           "<transport public key hex>",
  "signature":           "<130-hex EIP-712 from delegator>",
  "extraData":           "00"
}
```

The `signature` is signed by the **delegator** (the ciphertext owner), not the delegate.

### Key material

```text
GET /v2/keyurl
```

Returns the URLs for the active FHE public key and CRS — nested under `response`:

```json
{
  "status": "succeeded",
  "response": {
    "fheKeyInfo": [
      { "fhePublicKey": { "dataId": "...", "urls": ["https://..."] } }
    ],
    "crs": {
      "2048": { "dataId": "...", "urls": ["https://..."] }
    }
  }
}
```

The CRS map is keyed by ZK proof bit-size. Clients pick the right CRS for the bit size they're proving over (`2048` covers all current request sizes since `MAX_DECRYPTION_REQUEST_BITS = 2048`).

## Protocol limits to respect

Worth surfacing in clients before submission:

| Limit | Value | Where enforced |
|-------|-------|----------------|
| `MAX_USER_DECRYPT_CONTRACT_ADDRESSES` | `10` | Gateway `Decryption` |
| `MAX_USER_DECRYPT_DURATION_DAYS` | `365` | Gateway `Decryption` |
| `MAX_DECRYPTION_REQUEST_BITS` | `2048` (sum of plaintext bit-sizes in one decryption request) | Gateway `Decryption` |

## Validation pipeline

Performed before queuing:

1. **Chain ID** — for endpoints that take it, the chain must be a registered host chain. Fail → `400`.
2. **Host ACL** — multicall against the host ACL, grouped by chain:

| Operation | Check |
|-----------|-------|
| Public decryption | `ACL.isAllowedForDecryption(handle)` per handle |
| User decryption | `ACL.isAllowed(handle, userAddress)` AND `ACL.isAllowed(handle, contractAddress)` per pair |
| Delegated user decryption | `ACL.isHandleDelegatedForUserDecryption(delegator, delegate, contract, handle)` per pair (single call — internally checks delegator allow, contract allow, and delegation freshness) |

ACL failure → `400` with `error.label: "not_allowed_on_host_acl"`. RPC failure → `500` with `error.label: "host_acl_failed"`.

3. **Queue capacity** — overflow returns `429` with a `Retry-After` computed from queue depth and drain rate.

This Relayer pre-check is **non-authoritative** — the KMS Connector re-validates ACL against the host chain before forwarding to KMS Core. The Relayer's job is fast error reporting. See [./acl.md](./acl.md) for the full enforcement model.

## Request lifecycle

```text
POST /v2/{operation}
  → validate (chain, ACL)
  → request hash = SHA-256(normalised params)
  → dedup:
      active duplicate    → return same job_id
      completed duplicate → return stored result immediately
      new                 → insert "Queued"
  → 202 Accepted { requestId, status: "queued", Retry-After }

Background
  Queued → encode calldata, submit gateway tx
  TxInFlight → wait for receipt
  ReceiptReceived → blockchain listener watches for response event
  EventMatched → decode, persist result
  Succeeded | Failed | TimedOut(30 min)

GET /v2/{operation}/{job_id}
  Queued / Processing → 202 + Retry-After (queue-position-aware estimate)
  Succeeded → 200 + result
  Failed | TimedOut → 200 + error
```

## Gateway transactions

| Operation | Contract | Method |
|-----------|----------|--------|
| Input proof | `InputVerification` | `verifyProofRequest(contractChainId, contractAddress, userAddress, ciphertextWithZKProof, extraData)` |
| Public decryption | `Decryption` | `publicDecryptionRequest(ctHandles[], extraData)` |
| User decryption | `Decryption` | `userDecryptionRequest(ctHandleContractPairs[], requestValidity, contractsInfo, userAddress, publicKey, signature, extraData)` |
| Delegated user decryption | `Decryption` | `delegatedUserDecryptionRequest(ctHandleContractPairs[], requestValidity, delegationAccounts, contractsInfo, publicKey, signature, extraData)` |

Note: `delegationAccounts` is a single struct `{ delegatorAddress, delegateAddress }` that comes BEFORE `contractsInfo`.

## Gateway events listened for

| Event | Source | Relayer action |
|-------|--------|----------------|
| `VerifyProofResponse(zkProofId, ctHandles, signatures)` | `InputVerification` | Decode, store as `{ accepted: true, handles, signatures }` |
| `RejectProofResponse(zkProofId)` | `InputVerification` | Store as `{ accepted: false }` |
| `PublicDecryptionResponse(decryptionId, decryptedResult, signatures, extraData)` | `Decryption` | Decode, store |
| `UserDecryptionResponse(decryptionId, response, signature, extraData)` (per KMS node) | `Decryption` | Collect into a buffer keyed by `decryptionId` |
| `UserDecryptionResponseThresholdReached(decryptionId)` | `Decryption` | Mark the buffered shares for this `decryptionId` as complete |

User decryption is two events: per-node `UserDecryptionResponse` events carry the shares, then a payload-free `UserDecryptionResponseThresholdReached` event signals "you have enough — finalise this job."

## Back-pressure and deduplication

- **POST when full**: `429` with `Retry-After: <RFC 7231 timestamp>` from estimated drain time.
- **GET while processing**: `202` with `Retry-After: <seconds>` from request position and known coprocessor/KMS stage latencies (configurable via `copro_kms_backoff_intervals`).
- **Dedup**: request hash (SHA-256 of normalised params) drives a uniqueness index on active rows; succeeded-request hits return the stored result without reprocessing.

## Storage

PostgreSQL stores request parameters (for dedup), status transitions, response payloads (shares, plaintext, handles), and error details.
