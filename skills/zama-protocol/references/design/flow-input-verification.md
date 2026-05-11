# FHEVM: Input Verification Flow

When a user submits an encrypted value to a contract, they prove (in zero-knowledge) that they know its plaintext. The ZKPoK is verified off-chain by coprocessors; the contract only sees a verified handle.

## End-to-end

```text
User (browser / SDK)
  1. GET /v2/keyurl → FHE public key + CRS
  2. encrypt plaintext under FHE public key
  3. generate ZKPoK using CRS
  4. ciphertextWithInputVerification = abi(ciphertext, zkproof)
  5. POST /v2/input-proof
       { contractChainId, contractAddress, userAddress,
         ciphertextWithInputVerification, extraData }
        │
        ▼
Relayer
  - validate contractChainId is supported (no ACL check — input not yet committed)
  - queue, return 202 + job_id
  - background: submit
      InputVerification.verifyProofRequest(
          contractChainId, contractAddress, userAddress,
          ciphertextWithZKProof, extraData)
        │
        ▼
Gateway InputVerification
  emits VerifyProofRequest { zkProofId, contractChainId, contractAddress,
                             userAddress, ciphertextWithZKProof, extraData }
        │
        ▼
Each coprocessor (independently, via gw-listener)
  - load CRS from public keychain
  - verify ZKPoK (proof valid, prover knows plaintext)
  - compute handle, store ciphertext in S3
  - ECDSA-sign CiphertextVerification with its signerAddress
  - call verifyProofResponse(zkProofId, handles[], coprocessorSignature)
    or rejectProofResponse(zkProofId, ...) on failure
        │
        ▼
Gateway InputVerification consensus
  - dedup by (requestId, coprocessor) — alreadyResponded map
  - bucket responses by hash(zkProofId, handles[])
  - at coprocessorThreshold matching responses:
      emit VerifyProofResponse { zkProofId, accepted: true, handles[], signatures[] }
  - at coprocessorThreshold rejections:
      emit VerifyProofResponse { zkProofId, accepted: false }
        │
        ▼
Relayer (blockchain listener)
  stores result, marks job Completed

User polls GET /v2/input-proof/{job_id}
  → { accepted, handles[], signatures[] }

dApp (host chain)
  FHEVMExecutor.verifyInput(inputHandle, inputProof)
    → InputVerifier.verifyInputsEIP712KMSSignatures(...)
    → returns verified handle, usable in FHE ops
```

## Gateway: `InputVerification`

```solidity
event VerifyProofRequest(
    uint256 indexed zkProofId,
    uint256 indexed contractChainId,
    address contractAddress,
    address userAddress,
    bytes   ciphertextWithZKProof,
    bytes   extraData
);

function verifyProofResponse(uint256 requestId, bytes32[] handles, bytes coprocessorSignature) external;
function rejectProofResponse(uint256 requestId, bytes coprocessorSignature) external;
```

Consensus is established when `coprocessorThreshold` distinct coprocessors submit responses that hash to the same `(requestId, handles[])`. Duplicate submissions from a single coprocessor are rejected.

## Host chain: `InputVerifier`

```solidity
struct InputVerifierStorage {
    mapping(address => bool) isSigner;
    address[] signers;
    uint256 threshold;
}

function verifyInputsEIP712KMSSignatures(
    address userAddress,
    address contractAddress,
    bytes memory inputProof
) external returns (bytes32[] memory handles);
```

Steps:
1. Decode embedded coprocessor signatures from `inputProof`.
2. Reconstruct the `CiphertextVerification` EIP-712 struct (userAddress, contractAddress, handles, chain context).
3. `ecrecover` each signature; require signer ∈ `isSigner`; require unique-signer count ≥ `threshold`.
4. Return the verified handles.

Note: `InputVerifier` uses `EIP712UpgradeableCrossChain` — signatures created against the gateway's domain separator validate on any host chain.

## Failure modes

| Scenario | Result |
|----------|--------|
| Invalid ZKPoK | Coprocessors call `rejectProofResponse`; threshold of rejections → `VerifyProofResponse(accepted=false)` |
| Insufficient valid signatures on host | `InputVerifier` reverts |
| Unregistered signer | Signature ignored, not counted |
| Same coprocessor submits twice | Revert (`alreadyResponded`) |
| Stale request | Implementation-defined timeout |
