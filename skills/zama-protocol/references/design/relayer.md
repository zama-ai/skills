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

Pending requests respond `202` with a `Retry-After` header.

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
{ "handles": ["0x..."], "contractChainId": "<chain_id>", "extraData": "00" }
```

All handles must be marked publicly decryptable in the host ACL (validated before queuing).

Result: `{ "plaintext": "<abi-encoded>", "signatures": ["0x..."] }`.

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

Result: `{ "userDecryptedShares": ["..."], "signatures": ["0x..."] }`. The user combines shares client-side; see [./flow-user-decryption.md](./flow-user-decryption.md).

### Delegated user decryption

```text
POST /v2/delegated-user-decrypt
GET  /v2/delegated-user-decrypt/{job_id}
```

Same shape as user decryption, plus `delegatorAddress`, `delegateAddress`. **The `signature` field is signed by the delegator**, not the delegate.

### Key material

```text
GET /v2/keyurl
```

Returns the URLs for the active FHE public key and CRS. The client fetches them to encrypt inputs and generate ZK proofs.

```json
{ "fhePublicKeyUrl": "https://...", "crsUrl": "https://..." }
```

## Validation pipeline

Performed before queuing:

1. **Chain ID** — `contractChainId` is a registered host chain. Fail → `400`.
2. **Host ACL** — multicall against the host ACL, grouped by chain:

| Operation | Check |
|-----------|-------|
| Public decryption | `ACL.isAllowedForDecryption(handle)` per handle |
| User decryption | `ACL.isAllowed(handle, userAddress)` AND `ACL.isAllowed(handle, contractAddress)` per pair |
| Delegated user decryption | `ACL.isHandleDelegatedForUserDecryption(delegator, delegate, contract, handle)` per pair |

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
  Completed | Failed | TimedOut(30 min)

GET /v2/{operation}/{job_id}
  Queued / Processing → 202 + Retry-After (queue-position-aware estimate)
  Completed → 200 + result
  Failed | TimedOut → 200 + error
```

## Gateway transactions

| Operation | Contract | Method |
|-----------|----------|--------|
| Input proof | `InputVerification` | `verifyProofRequest(contractChainId, contractAddress, userAddress, ciphertextWithZKProof, extraData)` |
| Public decryption | `Decryption` | `publicDecryptionRequest(ctHandles[], extraData)` |
| User decryption | `Decryption` | `userDecryptionRequest(ctHandleContractPairs[], validity, contractsInfo, userAddress, publicKey, signature, extraData)` |
| Delegated user decryption | `Decryption` | `delegatedUserDecryptionRequest(ctHandleContractPairs[], validity, delegationAccounts, contractsInfo, publicKey, signature, extraData)` |

## Gateway events listened for

| Event | Source | Relayer action |
|-------|--------|----------------|
| `VerifyProofResponse(requestId, accepted, handles, signatures)` | `InputVerification` | Decode, store |
| `PublicDecryptionResponse(requestId, plaintext, signatures)` | `Decryption` | Decode plaintext, store |
| `UserDecryptionResponseThresholdReached(requestId, shares[], signatures[])` | `Decryption` | Store shares + signatures |

## Back-pressure and deduplication

- **POST when full**: `429` with `Retry-After: <RFC 7231 timestamp>` from estimated drain time.
- **GET while processing**: `202` with `Retry-After: <seconds>` from request position and known coprocessor/KMS stage latencies (configurable via `copro_kms_backoff_intervals`).
- **Dedup**: request hash (SHA-256 of normalised params) drives a uniqueness index on active rows; completed-request hits return the stored result without reprocessing.

## Storage

PostgreSQL stores request parameters (for dedup), status transitions, response payloads (shares, plaintext, handles), and error details.
