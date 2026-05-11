# FHEVM: Public Decryption Flow

Public decryption turns a handle into plaintext anyone can read. The contract must have called `ACL.allowForDecryption(handles[])` first.

## End-to-end

```text
dApp / User
  1. (prereq) contract called ACL.allowForDecryption(handles[])
  2. POST /v2/public-decrypt
       { handles[], contractChainId, extraData }
        │
        ▼
Relayer
  - contractChainId supported
  - multicall ACL.isAllowedForDecryption(handle) on host chain — 400 if any fails
  - queue, return 202 + job_id
  - background: Decryption.publicDecryptionRequest(ctHandles[], extraData)
        │
        ▼
Gateway: Decryption
  - require ctHandles.length > 0
  - getSnsCiphertextMaterials(handles) → require all handles use same keyId, all committed
  - assign decryptionId from publicDecryptionCounter
  - store publicCtHandles[decryptionId] = ctHandles[]
  - collect protocol fee via ProtocolPayment
  - emit PublicDecryptionRequest { decryptionId, ctHandles[], snsCiphertextMaterials[] }
        │
        ▼
Each KMS Connector (via gw-listener)
  - authoritative ACL re-check against host chain: ACL.isAllowedForDecryption(handle)
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
        │
        ▼
Gateway: Decryption consensus
  - reject if decryptionId > publicDecryptionCounter
  - verify EIP-712 signature, signer ∈ registered KMS nodes (GatewayConfig)
  - reject duplicates (kmsNodeAlreadySigned)
  - at publicDecryptionThreshold valid responses:
      decryptionDone[id] = true
      emit PublicDecryptionResponse { decryptionId, decryptedResult, signatures[], kmsSignerAddresses[] }
        │
        ▼
Relayer (blockchain listener)
  store { plaintext, signatures[] }; mark job Completed

User polls GET /v2/public-decrypt/{job_id} → { plaintext, signatures[] }
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

function isDecryptionDone(uint256 decryptionId) external view returns (bool);
```

`publicDecryptionRequest` does **not** return the `decryptionId` — the caller must listen for the `PublicDecryptionRequest` event to obtain it.

**Preconditions on the request:** `ctHandles.length > 0`; every handle committed in `CiphertextCommits`; all handles share the same `keyId`; protocol fee paid.

## EIP-712 verification

```solidity
struct PublicDecryptVerification {
    bytes32[] ctHandles;     // handles being decrypted
    bytes     decryptedResult; // abi-encoded plaintext values
    bytes     extraData;       // version byte + arbitrary data
}
```

Each KMS node signs this. The gateway verifies all signatures encode the same `decryptedResult` — that is the consensus check on the plaintext.

## Ciphertext material lookup

Before emitting the request event, `Decryption` calls `CiphertextCommits.getSnsCiphertextMaterials(handles)`. Each entry returns `{ ctHandle, keyId, snsCiphertextDigest }`. KMS connectors use the digest to retrieve the ciphertext from the originating coprocessor's S3.

## Consensus state

```solidity
mapping(uint256 => bool) decryptionDone;
mapping(uint256 => mapping(address => bool)) kmsNodeAlreadySigned;
mapping(uint256 => address[]) consensusTxSenderAddresses;
```

Once `decryptionDone[id] = true`, further responses are rejected.

## Fees

`ProtocolPayment` tracks per-operation fees via `OperationType { PublicDecrypt, UserDecrypt, InputVerification, KMSGeneration }`. Fee values are governance-configurable; collected fees go to the protocol treasury or burn address.
