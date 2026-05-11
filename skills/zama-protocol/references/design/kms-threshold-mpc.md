# KMS: Threshold MPC Protocols

Maliciously secure MPC for TFHE key management. Up to `t` parties may be Byzantine; security requires `n ≥ 3t + 1` (strong honest majority — required for malicious safety without a trusted setup).

Field arithmetic uses `Z64` (most operations) or `Z128` (large key operations). Secret shares are Shamir polynomials over the chosen ring; combination is Lagrange interpolation.

## Sessions

Each MPC execution runs in a session with correlated randomness and per-protocol preprocessing.

```rust
SmallSession<Z64>  { base, prss: SmallPrss, preprocessing: Option<SmallPreprocessing> }
LargeSession<Z128> { base, prss: LargePrss, preprocessing: Option<LargePreprocessing> }
```

`base` carries the peer network and party config; `prss` is the PRSS state (see below); `preprocessing` is the per-protocol offline material.

## PRSS

PRSS produces fresh shared randomness without online communication. Each pair `(i, j)` agrees a PRG seed `seed_{ij}` during setup (DH/OT). To produce a sharing of a fresh random value, each party `i` computes

```text
r_i = Σ_{j: j<i} PRG(seed_{ij}) − Σ_{j: j>i} PRG(seed_{ij})
```

This yields a valid Shamir sharing of `r` with `Σ r_i = 0`. O(n) local work, no online round trips.

## Distributed key generation (DKG)

Inputs: `n`, `t`, TFHE parameter modulus `q`.

```text
Preprocessing
  Each party i samples a secret degree-t polynomial f_i, using PRSS randomness.

Online
  1. Broadcast: each i broadcasts a Pedersen commitment C_i to f_i.
  2. Share distribution: each i sends encrypted f_i(j) to each j (mTLS).
  3. Verification: each j verifies Verify(C_i, j, f_i(j)). Failure → broadcast complaint.
  4. Dispute: if ≥ t+1 complaints against i, exclude i. Otherwise, the accused publishes f_i(j) publicly.
  5. Derive:
       sk_j = Σ_{honest i} f_i(j)            (party j's key share)
       pk   = Σ_{honest i} C_i[0]            (TFHE public key)
```

Outputs:
- `sk_j` — party j's share of the GLWE secret key.
- `pk` — TFHE public key, identical across parties, public.
- `server_key` — bootstrapping key, derived from `sk` via further threshold computation.

## Partial decryption (used by both public and user decryption)

For a TFHE ciphertext `ct = (a, b)`:

```text
each party i computes
  p_i = b + a · sk_i + noise_i
```

Fresh noise is required (noise flooding) — without it, observing partial decryptions leaks information about `sk_i`.

**Public decryption**: parties broadcast `p_i`; the coordinator (or each party) Lagrange-combines `Σ_{i∈S} L_i · p_i` and decodes `m = Round(p / Δ)`. Threshold is `t + 1`.

**User decryption**: parties do *not* broadcast `p_i`. Each instead:

```text
1. partial_i = b + a · sk_i + noise_i
2. package { partial_i, party_id: i, degree: t }
3. sign with the node's ECDSA key
4. signcrypt under the user's transport public key
5. submit signcrypted result on-chain via the connector
```

The user collects `2t + 1` distinct signcrypted shares, decapsulates each with their transport private key, verifies KMS signatures, then runs Lagrange interpolation + TFHE decoding client-side.

## Key resharing

Re-shares the existing secret key to a new party set while preserving the public key.

```text
For each old party i:
  g_i(x) = sk_i + a_1·x + … + a_t·x^t      (a_k fresh random)
  broadcast D_i = Commit(g_i)
  send encrypted g_i(j) to each new party j

For each new party j:
  verify Verify(D_i, j, g_i(j))
  sk'_j = Σ_{honest i} g_i(j)

Check: Σ D_i[0] == pk                     (public key unchanged)
```

Security: holds as long as ≤ t old AND ≤ t new parties are corrupted.

## CRS generation

Distributed powers-of-tau. Each party in turn applies a fresh scalar `r_i` to the running CRS and publishes a proof of knowledge of `r_i`. The final CRS encodes `r_1 · r_2 · … · r_N`. Sound as long as **one** party chose `r_i` randomly and erased it.

## Networking

Inter-node traffic uses mTLS; certificate CN matches `mpc_identity` set at node init, CA per `MpcContext`, peer routing via `external_url` on each `MpcNode`. Session IDs are derived as `H(request_id, protocol_name, party_ids)` and messages are tagged `(session_id, round)`. Sessions are ephemeral; serialization is `bincode`. No application-layer signing on messages — authentication is at the TLS layer.

## Performance (production / test parameters, `n = 4`)

| Operation | Production | Test |
|-----------|-----------|------|
| DKG preprocessing | hours | seconds |
| DKG online        | minutes | seconds |
| Public decryption | 1–10 s | 1–10 s |
| User decryption   | 1–10 s | 1–10 s |
| PRSS setup        | seconds | seconds |

Compute is Rayon-parallelised; `num_rayon_threads` controls the pool.

## Failure handling

| Failure | Response |
|---------|----------|
| Party drops mid-protocol | Abort and retry with remaining honest parties |
| Party sends invalid share | Detected by commitment verification; party excluded |
| Byzantine coordinator | Coordinator rotated; protocol retried |
| Network partition | Stall, auto-retry after timeout |
| Insufficient parties | gRPC `Unavailable`; retry on reconnect |
