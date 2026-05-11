# FHEVM: Coprocessor System

The coprocessor executes the actual TFHE computation and verifies user ZK proofs. It is purely event-driven — no public ingress, no user HTTP. Two listeners feed work in:

- `host-listener` — host-chain `FHEVMExecutor` events → schedule FHE compute
- `gw-listener` — gateway `InputVerification.VerifyProofRequest` → schedule ZKPoK verification

## Topology

```text
Host chain events           Gateway events
        │                         │
        ▼                         ▼
  host-listener            gw-listener
        │     PostgreSQL          │
        ▼          ▼               ▼
  tfhe-worker              zkproof-worker
  (FHE compute)            (ZKPoK verify)
        │                         │
  sns-worker                       │
  (switch & squash)               │
        └────────┬────────────────┘
                 ▼
          transaction-sender
          (gateway: addCiphertextMaterial, verifyProofResponse)
```

## Services

| Service | Role |
|---------|------|
| `host-listener` | Watches `FHEAdd/Mul/Sub/…`, `FHETrivialEncrypt`, `FHECast`, `ACL.*` events. Persists tasks. |
| `gw-listener` | Watches `InputVerification.VerifyProofRequest` and `KMSGeneration.*` (for server-key cache invalidation). |
| `tfhe-worker` | Fetches input ciphertexts from S3, loads server key (cached at startup), executes the TFHE op, writes output to S3, records result. Rayon thread pool. |
| `zkproof-worker` | Loads CRS, verifies the ZKPoK, computes input handles, stores ciphertext, signs with ECDSA. Rejects invalid proofs. |
| `sns-worker` | Switch-and-Squash: produces compact ciphertexts (smaller, faster for KMS to decrypt). Decryption always consumes the SNS form. |
| `transaction-sender` | Submits `InputVerification.verifyProofResponse` / `rejectProofResponse` and `CiphertextCommits.addCiphertextMaterial`. Configurable signer (raw key or AWS KMS), retry, nonce management. |

## Registration

Each coprocessor is registered in `GatewayConfig`:

```solidity
struct Coprocessor {
    address txSenderAddress;  // identifies the coprocessor for dedup in CiphertextCommits
    address signerAddress;    // verified by InputVerifier on signature recovery
    string  s3BucketUrl;      // public S3 endpoint, used by KMS connectors to fetch ciphertext
}
```

## Storage layout

```text
s3://bucket/ciphertexts/{handle_hex}        regular ciphertext
s3://bucket/sns_ciphertexts/{handle_hex}    SNS form (used for decryption)
```

`CiphertextCommits.getSnsCiphertextMaterials(handles[])` returns `snsCiphertextDigest` per handle, which identifies the object in the originating coprocessor's bucket.

## Consensus threshold

Multiple coprocessors run in parallel. The gateway accepts a ciphertext or input-proof result only once `coprocessorThreshold` distinct coprocessors submit matching responses (hash over `(requestId, handles[])` or `(commit, digest)`). A single compromised coprocessor cannot push a fraudulent commit.

Dependencies between ops are reconstructed from on-chain events — `tfhe-worker` will not execute B before A's output ciphertext exists. Independent ops batch concurrently.

## Trust model

- Coprocessors hold the **server key** (bootstrapping material) and the **CRS**. They never hold any secret-key share.
- They cannot decrypt — they can only compute on ciphertexts and produce new ciphertexts.
- SNS ciphertext digests are committed on-chain; KMS nodes verify the digest matches the fetched ciphertext before decryption.
