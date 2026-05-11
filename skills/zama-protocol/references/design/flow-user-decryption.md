# FHEVM: User Decryption (and Delegated)

User decryption returns plaintext only to a specific user. Plaintext is never on-chain. Each KMS node produces a partial decryption share, signed and signcrypted under an ephemeral user transport key; the user reconstructs the plaintext client-side from `t+1` shares (or more, per `userDecryptionThreshold`).

Delegated user decryption extends this so a delegate can submit the request, provided the delegator has already called `ACL.delegateForUserDecryption(delegate, contract, expirationDate)`.

## End-to-end (user decryption)

```text
User (browser / SDK)
  1. generate ephemeral transport keypair (E2eTransportKeypair, ML-KEM-style)
  2. build UserDecryptRequestVerification (EIP-712):
       { publicKey, contractAddresses[], startTimestamp, durationDays }
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
  - contractAddresses.length ∈ [1, 10]
  - userAddress ∉ contractAddresses
  - startTimestamp ≤ block.timestamp ≤ startTimestamp + durationDays * 86400
  - each handle's chainId matches its paired contract's host chain
  - EIP-712 signature recovers to userAddress
  - all handles share same keyId (from getSnsCiphertextMaterials)
  - assign userDecryptionId; store { publicKey, ctHandles[] }; collect fee
  - emit UserDecryptionRequest {
        userDecryptionId, userAddress, publicKey,
        snsCiphertextMaterials[], requestValidity, extraData }
        │
        ▼
Each KMS Connector
  - authoritative ACL re-check against host chain: user AND contract allowed per handle
  - gRPC: UserDecrypt(requestId, ciphertexts[], keyId, clientAddress, transportPk, domain)
        │
        ▼
Each KMS Core node
  - load secret-key share for keyId
  - compute partial decryption per ciphertext
  - sign the share with the node's ECDSA key
  - signcrypt the signed share under the user's transport public key
  - produce UserDecryptionResponsePayload {
        verification_key, digest, signcrypted_ciphertexts[], party_id, degree }
  - EIP-712 sign UserDecryptResponseVerification {
        publicKey, ctHandles[], userDecryptedShare, extraData }
        │
        ▼
KMS Connector calls
  Decryption.userDecryptionResponse(
      userDecryptionId, userDecryptedShare, signature, extraData)
        │
        ▼
Gateway: Decryption consensus
  - require userDecryptionId ≤ userDecryptionCounter
  - reload stored publicKey
  - verify EIP-712, signer ∈ registered KMS, no duplicate (kmsNodeAlreadySigned)
  - at userDecryptionThreshold valid responses:
      emit UserDecryptionResponseThresholdReached {
          userDecryptionId, userDecryptedShares[], signatures[], kmsSignerAddresses[] }
        │
        ▼
Relayer (blockchain listener)
  store shares + signatures; mark job Completed

User polls GET /v2/user-decrypt/{job_id}
  → { userDecryptedShares[], signatures[] }

User (client-side reconstruction)
  for each share:
    signedPayload = signcryption-decapsulate(transportPrivateKey, share)
    verify KMS ECDSA signature on signedPayload
  reconstruct plaintext via Lagrange interpolation over (party_id, partial_i),
  applying the TFHE decoding step (Round((Σ L_i · partial_i) / Δ))
```

## Delegated user decryption

Same flow, with the delegate submitting the request and the **delegator's** EIP-712 signature.

```text
POST /v2/delegated-user-decrypt
  { handleContractPairs[], requestValidity, contractsChainId,
    contractAddresses[],
    delegatorAddress,    // ciphertext owner
    delegateAddress,     // caller
    publicKey, signature, extraData }

Relayer ACL check (per pair):
  ACL.isHandleDelegatedForUserDecryption(delegator, delegate, contract, handle)

Relayer submits:
  Decryption.delegatedUserDecryptionRequest(
      ctHandleContractPairs[], requestValidity, contractsInfo,
      delegatorAddress, delegateAddress, publicKey,
      delegatorSignature, extraData)
```

Additional contract validation:
1. `ACL.isDelegatedForUserDecryption(delegator, delegate, contract)` is true and not expired.
2. EIP-712 signature is over `DelegatedUserDecryptRequestVerification` (which includes `delegatorAddress`) and recovers to the delegator.

Past this point, the flow is identical to standard user decryption.

## EIP-712 structs

```solidity
struct UserDecryptRequestVerification {
    bytes publicKey;             // user's transport public key (signcryption target)
    address[] contractAddresses; // 1..10
    uint256 startTimestamp;
    uint256 durationDays;
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
    uint256 startTimestamp;
    uint256 durationDays;
    address delegatorAddress;
}
```

## Validity window

```text
valid_from  = startTimestamp
valid_until = startTimestamp + durationDays * 86400
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

## Security invariants (specific to user decryption)

- Plaintext is never on-chain — only signcrypted shares are.
- Reconstruction requires `userDecryptionThreshold` distinct shares; no single node can decrypt.
- Each share is ECDSA-signed by its KMS node — forgery requires breaking ECDSA + the threshold.
- Contract scope: each request lists explicit contracts; handles outside that set cannot be decrypted under this request.
- Delegation expires (block timestamp), and `ACL` blocks delegate/revoke within the same block as a decryption to prevent flash-style attacks.
