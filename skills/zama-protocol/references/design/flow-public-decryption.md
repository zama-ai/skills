# FHEVM: Public Decryption Flow

Public decryption turns a handle into plaintext anyone can read. The contract must have called `FHE.makePubliclyDecryptable(handle)` (which maps to `ACL.allowForDecryption(handles[])`) first.

## End-to-end

```text
dApp / User
  1. (prereq) contract called FHE.makePubliclyDecryptable(handle)
  2. POST /v2/public-decrypt
       { ciphertextHandles, extraData }
        │
        ▼
Relayer
  - multicall ACL.isAllowedForDecryption(handle) on host chain — 400 if any fails
  - queue, return 202 + job_id
  - background: Decryption.publicDecryptionRequest(ctHandles[], extraData)
        │
        ▼
Gateway: Decryption
  - require ctHandles.length > 0
  - require sum of plaintext bit sizes ≤ MAX_DECRYPTION_REQUEST_BITS (2048)
  - getSnsCiphertextMaterials(handles) → require all handles use same keyId, all committed
  - assign decryptionId from publicDecryptionCounter
  - collect protocol fee via ProtocolPayment._collectPublicDecryptionFee
  - emit PublicDecryptionRequest(decryptionId, snsCtMaterials, extraData)
        │
        ▼
Each KMS Connector (via gw-listener)
  - authoritative ACL re-check on host chain: ACL.isAllowedForDecryption(handle)
  - fetch ciphertexts from coprocessor S3 via snsCiphertextDigest
  - gRPC (localhost): PublicDecrypt(requestId, typedCiphertexts[], keyId, domain, contextId, epochId)
        │
        ▼
Each KMS Core node
  - load secret-key share for keyId
  - compute partial decryption with noise flooding
  - threshold combine (Lagrange) → plaintext
  - EIP-712 sign PublicDecryptVerification { ctHandles[], decryptedResult, extraData }
        │
        ▼
KMS Connector
  Decryption.publicDecryptionResponse(decryptionId, decryptedResult, signature, extraData)
  → contract emits a per-call PublicDecryptionResponseCall event (every KMS submission)
        │
        ▼
Gateway: Decryption consensus
  - reject if decryptionId > publicDecryptionCounter
  - verify EIP-712 signature, signer ∈ registered KMS nodes (GatewayConfig)
  - reject duplicates (kmsNodeAlreadySigned)
  - at publicDecryptionThreshold valid responses:
      decryptionDone[id] = true
      emit PublicDecryptionResponse(decryptionId, decryptedResult, signatures[], extraData)
        │
        ▼
Relayer (blockchain listener)
  store { decryptedValue, signatures[], extraData }; mark job Completed

User polls GET /v2/public-decrypt/{job_id} → { decryptedValue, signatures[], extraData }
```

## Contract API

```solidity
function publicDecryptionRequest(
    bytes32[] calldata ctHandles,
    bytes calldata extraData
) external whenNotPaused;

function publicDecryptionResponse(
    uint256 decryptionId,
    bytes calldata decryptedResult,
    bytes calldata signature,
    bytes calldata extraData
) external;

function isPublicDecryptionReady(
    bytes32[] calldata ctHandles,
    bytes calldata extraData
) external view returns (bool);

function isDecryptionDone(uint256 decryptionId) external view returns (bool);
```

`publicDecryptionRequest` does **not** return the `decryptionId` — the caller must listen for the `PublicDecryptionRequest` event to obtain it. `isPublicDecryptionReady` is useful before submitting a request: it returns true when the gateway already has the SNS materials committed for every handle.

**Preconditions on the request:** `ctHandles.length > 0`; every handle has committed SNS material in `CiphertextCommits`; all handles share the same `keyId`; sum of plaintext bit sizes ≤ `MAX_DECRYPTION_REQUEST_BITS = 2048`; protocol fee paid.

## Events

```solidity
event PublicDecryptionRequest(
    uint256 indexed decryptionId,
    SnsCiphertextMaterial[] snsCtMaterials,
    bytes extraData
);

// emitted on every KMS-node submission (before threshold)
event PublicDecryptionResponseCall(
    uint256 indexed decryptionId,
    bytes decryptedResult,
    bytes signature,
    bytes extraData
);

// emitted once threshold is reached
event PublicDecryptionResponse(
    uint256 indexed decryptionId,
    bytes decryptedResult,
    bytes[] signatures,
    bytes extraData
);
```

The request event does not separately list `ctHandles[]` — each `SnsCiphertextMaterial` carries `ctHandle` along with `keyId` and `snsCiphertextDigest`.

## EIP-712 verification

```solidity
struct PublicDecryptVerification {
    bytes32[] ctHandles;        // handles being decrypted
    bytes     decryptedResult;  // abi-encoded plaintext values
    bytes     extraData;        // version byte + arbitrary data
}
```

Each KMS node signs this. The gateway verifies all signatures encode the same `decryptedResult` — that is the consensus check on the plaintext.

## Ciphertext material lookup

Before emitting the request event, `Decryption` calls `CiphertextCommits.getSnsCiphertextMaterials(handles)`. Each entry returns `{ ctHandle, keyId, snsCiphertextDigest, coprocessorTxSenderAddresses }`. KMS connectors use the digest to retrieve the ciphertext from the originating coprocessor's S3.

## Consensus state

```solidity
mapping(uint256 => bool) decryptionDone;
mapping(uint256 => mapping(address => bool)) kmsNodeAlreadySigned;
mapping(uint256 => mapping(bytes32 digest => address[])) consensusTxSenderAddresses;
```

The `consensusTxSenderAddresses` map is keyed by `(decryptionId, response-digest)` so the contract can track multiple competing answer buckets and only finalise when one bucket reaches threshold. Once `decryptionDone[id] = true`, further responses are rejected.

## Fees

`ProtocolPayment` collects a per-operation fee via `_collectPublicDecryptionFee` (separate function per operation type — there is no single `OperationType`-keyed table). The fee amount is governance-configurable; collected fees go to the protocol treasury or burn address.
