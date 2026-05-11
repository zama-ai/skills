# FHEVM: Handle System

A handle is a 32-byte deterministic commitment that identifies an encrypted value. The plaintext and ciphertext are never embedded — the ciphertext lives in coprocessor S3 storage keyed by the handle digest.

## Format

```text
Byte index:  [0..20]   [21]    [22..29]          [30]       [31]
Content:     random    index   chain ID (uint64) FHE type   version
             21 bytes  (0x00)  big-endian        1 byte     1 byte
```

The random prefix comes from a truncated keccak256 of the computation inputs. The lower 11 bytes are metadata, deterministically overwritten.

## Extraction (host code)

```solidity
// chainId (bits 16..79)
uint256 chainId = uint256((uint256(handle) >> 16) & 0xFFFFFFFFFFFFFFFF);

// fheType (bits 8..15)
FheType fheType = FheType(uint8(uint256((handle << 240) >> 248)));
```

Implemented in `HandleOps.sol` and used throughout validation.

## Generation

**Computation handles** (deterministic FHE ops):

```text
hash = keccak256(
    "FHE_comp" || opcode || lhs || rhs || scalarByte || acl || chainId || blockhash(block.number - 1)
)
handle = hash[:21] || 0x00 || chainId || fheType || version
```

**Randomness handles** (`fheRand`, `fheRandBounded`):

```text
keccak256("FHE_seed" || counterRand++ || fheType)
```

Per-contract monotonic counter — no `blockhash` input.

**Trivial encryption handles** (`trivialEncrypt(pt, fheType)`):

```text
keccak256("FHE_comp" || TRIVIAL_ENCRYPT_OPCODE || plaintext || fheType)
```

**Input handles**: computed by coprocessors from the user's ZKPoK and confirmed via threshold consensus on the gateway, then accepted by `FHEVMExecutor.verifyInput`.

## Collision resistance: why `blockhash` is in the preimage

Of the 32 bytes in a handle, 21 carry hash output and 11 carry metadata. 168 bits gives a birthday bound near 2⁸⁴ — short of the 128-bit target. Before `blockhash` was mixed in, the preimage was fully deterministic and known before transaction submission:

```text
op_hash = hash(operation_type, *argument_handles, chain_id)
```

An attacker could grind for a collision offline, then submit a colliding input. A collision means two distinct ciphertexts share a handle — subsequent ops silently use the wrong ciphertext.

Mixing in `blockhash(block.number - 1)` makes the preimage unpredictable until the previous block lands. The attacker has at most one block of wall-clock time after the hash is revealed to find a collision and get it on-chain. 2⁸⁴ work within a block time is infeasible. Block proposers see the hash earliest but face the same 2⁸⁴ bound within their proposal window. Gas overhead: `BLOCKHASH` (20) + one extra word in the encode (6) ≈ 26 gas per op.

This applies to all FHE compute handles via `_binaryOp`, `_unaryOp`, `_ternaryOp` in `FHEVMExecutor`. Excluded: `cast`, `trivialEncrypt`, and the `_generateSeed` path used by `fheRand` / `fheRandBounded` — these use different preimages.

`prevrandao` was considered as an alternative source of unpredictability but rejected as the sole input — some rollups return a constant `prevrandao`, leaving those deployments unprotected. Block hash is reliable across all supported chains; `prevrandao` could be added in addition where available for marginally independent entropy.

After a reorg, the same FHE op produces a different handle because the previous block hash differs — stale ciphertexts can't be confused with new ones. The threat-model edge case (op lands in the same position relative to the fork point) keeps the same handle and ciphertext.

## Validation (per operation)

`FHEVMExecutor` reverts unless:

1. Handle `chainId == block.chainid`
2. FHE type matches the operation's expected input type
3. Version byte is recognized
4. `ACL.isAllowed(handle, msg.sender)` is true
5. The op's HCU cost fits the per-tx and per-block budgets

## Treat handles as opaque

The protocol commits to **exactly one** property of handle values:

- **Identical handles ⇒ identical plaintext values** (even if the underlying ciphertexts differ).

Everything else is subject to change between releases. Application code must not rely on any other handle property.

### What you must not assume

For **computations**:

- *Same op on same inputs ⇒ same output handle.* Not true: `blockhash` is mixed in, so re-execution in a different block produces a different handle.
- *Different ops on same inputs ⇒ different handles.* Not guaranteed: a future constant-propagation pass could collapse `Add(h2, h0)` and `Add(h0, h2)` to the same handle, or `Select` on a trivial condition could fold to one branch.

For **ciphertexts**:

- *Same handle ⇒ same ciphertext.* The coprocessor may re-randomize at any point.
- *Different handles ⇒ different ciphertexts.* Trivial-op optimization or cross-chain bridging may copy a ciphertext under a new handle.

### Practical rules

- Do not compare handle values for equality in application logic.
- Do not hash handles or use them as map keys when the goal is plaintext-equality reasoning.
- Treat the bytes of a handle as an opaque identifier, like a memory pointer.

How handles are computed is an internal implementation detail and may change in any release. The protocol's correctness and security do not depend on application behaviour here — this rule exists to keep deployed applications from breaking when the protocol evolves.
