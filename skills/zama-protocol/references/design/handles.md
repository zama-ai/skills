# FHEVM: Handle System

A handle is a 32-byte deterministic commitment that identifies an encrypted value. The plaintext and ciphertext are never embedded — the ciphertext lives in coprocessor S3 storage keyed by the handle digest.

## Format

```text
Byte index:  [0..20]    [21]     [22..29]          [30]       [31]
Content:     random     index    chain ID (uint64) FHE type   version
             21 bytes   1 byte   big-endian        1 byte     1 byte
```

The top 21 bytes come from a truncated keccak256 of the computation inputs. The remaining 11 bytes are metadata, deterministically overwritten in `_appendMetadataToPrehandle`.

**Byte 21 is `0xff`** for any handle that comes from `FHEVMExecutor` computation (binary, unary, ternary, n-ary, cast, trivialEncrypt, fheRand). It distinguishes computation outputs from user-input handles where the byte indexes individual handles within an input batch.

## Extraction (host code)

```solidity
// chainId (bits 16..79)
uint256 chainId = uint256((uint256(handle) >> 16) & 0xFFFFFFFFFFFFFFFF);

// fheType (bits 8..15)
FheType fheType = FheType(uint8(uint256((handle << 240) >> 248)));
```

Implemented in `HandleOps.sol` and used throughout validation.

## Generation

The hash preimage for **every computation-derived handle** (binary, unary, ternary, n-ary, cast, trivial encryption, randomness) includes `blockhash(block.number - 1)` AND `block.timestamp`. Both are needed to defeat offline collision grinding (see "Collision resistance" below).

**Binary ops** (`fheAdd`, `fheSub`, `fheMul`, `fheBitAnd`, `fheEq`, `fheMin`, `fheShl`, …):

```text
keccak256(
    "FHE_comp" || opcode || lhs || rhs || scalarByte || ACL
    || block.chainid || blockhash(block.number - 1) || block.timestamp
)
```

**Unary ops** (`fheNeg`, `fheNot`):

```text
keccak256(
    "FHE_comp" || opcode || ct || ACL
    || block.chainid || blockhash(block.number - 1) || block.timestamp
)
```

**Ternary ops** (`fheIfThenElse`):

```text
keccak256(
    "FHE_comp" || opcode || control || ifTrue || ifFalse || ACL
    || block.chainid || blockhash(block.number - 1) || block.timestamp
)
```

**N-ary ops** (`fheSum`, `fheIsIn`): preimage includes the `bytes32[] values` array (and for `fheIsIn`, the singleton `value` operand).

**Cast** (`cast(ct, toType)`):

```text
keccak256(
    "FHE_comp" || CAST_OPCODE || ct || toType || ACL
    || block.chainid || blockhash(block.number - 1) || block.timestamp
)
```

**Trivial encryption** (`trivialEncrypt(pt, fheType)`):

```text
keccak256(
    "FHE_comp" || TRIVIAL_ENCRYPT_OPCODE || pt || fheType || ACL
    || block.chainid || blockhash(block.number - 1) || block.timestamp
)
```

**Randomness seed** (`fheRand`, `fheRandBounded`), via `_generateSeed`:

```text
keccak256(
    "FHE_seed" || counterRand || ACL
    || block.chainid || blockhash(block.number - 1) || block.timestamp
)
```

`counterRand` is a per-`FHEVMExecutor` monotonic counter, incremented per call. **The seed preimage does not include `fheType`** — the type is mixed in only when deriving the final randomness handle from the seed.

**Input handles**: not derived from this scheme. They're computed by coprocessors from the user's ZKPoK and confirmed via threshold consensus on the gateway, then accepted by `FHEVMExecutor.verifyInput`. The 21-byte prefix comes from the ZKPoK verification, byte 21 indexes the handle within the input batch (`0x00`, `0x01`, ...), and the metadata bytes follow the same layout.

## Collision resistance: why `blockhash` and `block.timestamp` are in the preimage

Of the 32 bytes in a handle, 21 carry hash output and 11 carry metadata. 168 bits gives a birthday bound near 2⁸⁴ — short of the 128-bit target. Without unpredictable inputs, the preimage would be fully deterministic and an attacker could grind for a collision offline, then submit a colliding input. A collision means two distinct ciphertexts share a handle — subsequent ops silently use the wrong ciphertext.

Mixing in `blockhash(block.number - 1)` and `block.timestamp` makes the preimage unpredictable until the previous block lands. The attacker has at most one block of wall-clock time after the values are revealed to find a collision and get it on-chain. 2⁸⁴ work within a block time is infeasible. Block proposers see these values earliest but face the same 2⁸⁴ bound within their proposal window. Gas overhead per op is negligible (a `BLOCKHASH`, a `TIMESTAMP`, and two extra words in the encode).

After a reorg, the same FHE op produces a different handle because both the previous block hash and the timestamp differ — stale ciphertexts can't be confused with new ones. `prevrandao` was considered as an alternative source of unpredictability but rejected as the sole input — some rollups return a constant `prevrandao`, leaving those deployments unprotected. Block hash is reliable across all supported chains.

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

- *Same op on same inputs ⇒ same output handle.* Not true: `blockhash` and `block.timestamp` are mixed in, so re-execution in a different block produces a different handle.
- *Different ops on same inputs ⇒ different handles.* Not guaranteed: a future constant-propagation pass could collapse `Add(h2, h0)` and `Add(h0, h2)` to the same handle, or `Select` on a trivial condition could fold to one branch.

For **ciphertexts**:

- *Same handle ⇒ same ciphertext.* The coprocessor may re-randomize at any point.
- *Different handles ⇒ different ciphertexts.* Trivial-op optimization or cross-chain bridging may copy a ciphertext under a new handle.

### Practical rules

- Do not compare handle values for equality in application logic.
- Do not hash handles or use them as map keys when the goal is plaintext-equality reasoning.
- Treat the bytes of a handle as an opaque identifier, like a memory pointer.

How handles are computed is an internal implementation detail and may change in any release. The protocol's correctness and security do not depend on application behaviour here — this rule exists to keep deployed applications from breaking when the protocol evolves.
