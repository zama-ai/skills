# FHEVM: User Decryption (and Delegated)

User decryption returns plaintext only to a specific user. Plaintext is never on-chain. Each KMS node produces a partial decryption share, signed and signcrypted under an ephemeral user transport key; the user reconstructs the plaintext client-side from `t+1` shares — the gateway emits `UserDecryptionResponseThresholdReached` once `userDecryptionThreshold = 2t+1` valid responses have been collected.

Delegated user decryption extends this so a delegate can submit the request, provided the delegator has already called `FHE.delegateUserDecryption(delegate, contract, expirationDate)` (or one of its variants) on the host chain.

## End-to-end (user decryption)

```text
User (browser / SDK)
  1. generate ephemeral transport keypair (SDK: client.generateTransportKeypair(), ML-KEM-style)
  2. build UserDecryptRequestVerification (EIP-712):
       { publicKey, contractAddresses[], startTimestamp, durationDays, extraData }
  3. sign with Ethereum wallet → userSignature
  4. POST /v2/user-decrypt
       { handleContractPairs: [{ handle, contractAddress }, ...],   // max 10 contracts
         requestValidity: { startTimestamp, durationDays },
         contractsChainId, contractAddresses[], userAddress,
         publicKey, signature, extraData }
        │
        ▼
Relayer
  - contractsChainId supported
  - per handle/contract pair: ACL.isAllowed(handle, userAddress)
    AND ACL.isAllowed(handle, contractAddress)
  - 400 if any ACL check fails; otherwise queue + 202
  - background: Decryption.userDecryptionRequest(
        ctHandleContractPairs[], requestValidity, contractsInfo,
        userAddress, publicKey, userSignature, extraData)
        │
        ▼
Gateway: Decryption validates
  - contractAddresses.length ∈ [1, MAX_USER_DECRYPT_CONTRACT_ADDRESSES] (=10)
  - durationDays ≤ MAX_USER_DECRYPT_DURATION_DAYS (=365)
  - userAddress ∉ contractAddresses
  - startTimestamp ≤ block.timestamp ≤ startTimestamp + durationDays * 86400
  - each handle's chainId matches its paired contract's host chain
  - sum of plaintext bit sizes ≤ MAX_DECRYPTION_REQUEST_BITS (=2048)
  - EIP-712 signature recovers to userAddress
  - all handles share same keyId (from getSnsCiphertextMaterials)
  - assign userDecryptionId; collect fee
  - emit UserDecryptionRequest(
        decryptionId, snsCtMaterials, userAddress, publicKey, extraData)
        │
        ▼
Each KMS Connector
  - authoritative ACL re-check on host chain: ACL.isAllowed(handle, user) AND
    ACL.isAllowed(handle, contract) per pair
  - gRPC: UserDecrypt(requestId, ciphertexts[], keyId, clientAddress, transportPk, domain)
        │
        ▼
Each KMS Core node
  - load secret-key share for keyId
  - compute partial decryption per ciphertext
  - sign the share with the node's ECDSA key
  - signcrypt the signed share under the user's transport public key
  - EIP-712 sign UserDecryptResponseVerification {
        publicKey, ctHandles[], userDecryptedShare, extraData }
        │
        ▼
KMS Connector calls
  Decryption.userDecryptionResponse(
      userDecryptionId, userDecryptedShare, signature, extraData)
  → contract emits per-call UserDecryptionResponse(decryptionId, response, signature, extraData)
        │
        ▼
Gateway: Decryption consensus
  - require userDecryptionId ≤ userDecryptionCounter
  - verify EIP-712, signer ∈ registered KMS, no duplicate (kmsNodeAlreadySigned)
  - at userDecryptionThreshold (2t+1) valid responses:
      emit UserDecryptionResponseThresholdReached(decryptionId)
        │
        ▼
Relayer (blockchain listener)
  collects the per-call UserDecryptionResponse events for this decryptionId
  (the ThresholdReached event carries no payload — it's only a signal)
  stores shares + signatures; mark job Completed

User polls GET /v2/user-decrypt/{job_id}
  → { result: [{ payload, signature, extraData }, ...] }

User (client-side reconstruction)
  for each share:
    signedPayload = signcryption-decapsulate(transportPrivateKey, payload)
    verify KMS ECDSA signature on signedPayload
  reconstruct plaintext via Lagrange interpolation over (party_id, partial_i),
  applying the TFHE decoding step (Round((Σ L_i · partial_i) / Δ))
```

## Delegated user decryption

Same flow, with the delegate submitting the request and the **delegator's** EIP-712 signature.

```text
POST /v2/delegated-user-decrypt
  { handleContractPairs[], startTimestamp, durationDays, contractsChainId,
    contractAddresses[],
    delegatorAddress,    // ciphertext owner
    delegateAddress,     // caller
    publicKey, signature, extraData }

Relayer ACL check (per pair):
  ACL.isHandleDelegatedForUserDecryption(delegator, delegate, contract, handle)
  // single call — internally checks delegator allow, contract allow, and
  // delegation freshness; no separate isAllowed calls

Relayer submits:
  Decryption.delegatedUserDecryptionRequest(
      ctHandleContractPairs[], requestValidity,
      delegationAccounts,      // struct { delegatorAddress, delegateAddress }
      contractsInfo,
      publicKey, delegatorSignature, extraData)
```

Note: `delegationAccounts` is a **single struct** carrying both addresses, and it comes BEFORE `contractsInfo` in the argument list. Additional contract validation:

1. `ACL.isHandleDelegatedForUserDecryption(delegator, delegate, contract, handle)` is true for every pair (the connector re-checks this authoritatively).
2. The delegation has not expired (`block.timestamp ≤ expirationDate`).
3. EIP-712 signature is over `DelegatedUserDecryptRequestVerification` and recovers to the delegator.

Past this point, the flow is identical to standard user decryption.

## EIP-712 structs

Field order is significant — the type hash and signature reconstruction depend on it.

```solidity
struct UserDecryptRequestVerification {
    bytes publicKey;             // user's transport public key
    address[] contractAddresses; // 1..10
    uint256 startTimestamp;
    uint256 durationDays;
    bytes extraData;             // version byte + arbitrary data
}

struct UserDecryptResponseVerification {
    bytes publicKey;
    bytes32[] ctHandles;
    bytes userDecryptedShare;    // serialized signcrypted payload from one KMS node
    bytes extraData;
}

struct DelegatedUserDecryptRequestVerification {
    bytes publicKey;
    address[] contractAddresses;
    address delegatorAddress;    // comes BEFORE startTimestamp
    uint256 startTimestamp;
    uint256 durationDays;
    bytes extraData;
}
```

## Validity window

```text
valid_from  = startTimestamp
valid_until = startTimestamp + durationDays * 86400
durationDays ≤ MAX_USER_DECRYPT_DURATION_DAYS (= 365)
```

Contract enforces `valid_from ≤ block.timestamp ≤ valid_until`. Prevents indefinite replay of a user signature.

## Storage

```solidity
struct UserDecryptionPayload {
    bytes publicKey;        // user's transport public key
    bytes32[] ctHandles;
}

mapping(uint256 => UserDecryptionPayload) userDecryptionPayloads;
mapping(uint256 => mapping(address => bool)) kmsNodeAlreadySigned;
```

## Events

```solidity
event UserDecryptionRequest(
    uint256 indexed decryptionId,
    SnsCiphertextMaterial[] snsCtMaterials,
    address userAddress,
    bytes publicKey,
    bytes extraData
);

// emitted per KMS-node submission, before threshold
event UserDecryptionResponse(
    uint256 indexed decryptionId,
    bytes response,
    bytes signature,
    bytes extraData
);

// emitted once at threshold — payload-free signal
event UserDecryptionResponseThresholdReached(uint256 indexed decryptionId);
```

The Relayer's blockchain listener watches both: per-call events to collect the shares, threshold event to mark the job complete.

## `isUserDecryptionReady` getter

```solidity
function isUserDecryptionReady(
    address userAddress,
    CtHandleContractPair[] calldata ctHandleContractPairs,
    bytes calldata extraData
) external view returns (bool);
```

Returns true when every handle in the batch is committed and ACL-allowed for both the user and its paired contract. Useful for clients before submitting.

## Security invariants (specific to user decryption)

- Plaintext is never on-chain — only signcrypted shares are.
- Reconstruction requires at least `t+1` distinct shares; gateway emits `ThresholdReached` once `2t+1` valid responses are stored. No single node can decrypt.
- Each share is ECDSA-signed by its KMS node — forgery requires breaking ECDSA + the threshold.
- Contract scope: each request lists explicit contracts; handles outside that set cannot be decrypted under this request.
- Delegation expires (block timestamp), and `ACL` blocks two delegate/revoke changes within the same block. The same-block rule does **not** prevent a decryption from happening in the same block as a delegation — only conflicting delegation-state changes.
