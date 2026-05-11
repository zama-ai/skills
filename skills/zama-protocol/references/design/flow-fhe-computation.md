# FHEVM: FHE Operations and Symbolic Execution

`FHEVMExecutor` is the on-chain symbolic execution engine. It does **no** cryptographic work — it validates inputs, charges HCU, generates a deterministic output handle, and emits an event. The coprocessor's `host-listener` picks the event up and runs the actual TFHE op off-chain. The handle is usable immediately by subsequent FHE calls; only decryption waits for the coprocessor.

## Operations

### Binary (`(bytes32 lhs, bytes32 rhs, bytes1 scalarByte)`)

```text
fheAdd · fheSub · fheMul · fheDiv · fheRem      arithmetic
fheBitAnd · fheBitOr · fheBitXor                bitwise
fheShl · fheShr · fheRotl · fheRotr             shift / rotate
fheEq · fheNe · fheLt · fheLe · fheGt · fheGe   comparison → ebool
fheMin · fheMax                                 min / max (still standard binary)
```

`scalarByte`:
- `0x00` — both operands are encrypted handles
- `0x01` — RHS is a plaintext scalar (raw bytes in place of `rhs`)

`fheDiv` and `fheRem` only accept scalar mode (encrypted divisor is not supported).

### Unary

`fheNeg(bytes32 ct)`, `fheNot(bytes32 ct)`.

### Ternary / control flow

`fheIfThenElse(bytes32 control, bytes32 ifTrue, bytes32 ifFalse)` — `control` is an `ebool`. Both branches always execute. The contract cannot branch on encrypted booleans any other way.

### Type / encoding

```solidity
function cast(bytes32 ct, FheType toType)                                returns (bytes32);
function trivialEncrypt(uint256 pt, FheType toType)                      returns (bytes32);
function verifyInput(
    bytes32 inputHandle,
    address userAddress,
    bytes inputProof,
    FheType inputType
) returns (bytes32);
```

`trivialEncrypt` is visible to anyone reading the chain — for constants and defaults only. `verifyInput` is what dApps call after the user obtained `handles[] + inputProof` from `/v2/input-proof`; it returns a single verified handle.

### Randomness

```solidity
function fheRand(FheType randType)                            returns (bytes32);
function fheRandBounded(uint256 upperBound, FheType randType) returns (bytes32);
```

`upperBound` must be a power of 2 (e.g. `128`, not `100`).

### Aggregates (n-ary)

```solidity
function fheSum(bytes32[] values, FheType resultType) returns (bytes32);
function fheIsIn(bytes32 value, bytes32[] values, FheType valueType) returns (bytes32); // result is ebool
```

Array length is bounded per FHE type (`FHE_COLLECTION_WIDE_MAX_SIZE` / `FHE_COLLECTION_NARROW_MAX_SIZE` in `FHEVMExecutor`). Large types (`euint256`+) have stricter caps than small ones.

## Handle generation

```text
binary / ternary / n-ary / cast / trivialEncrypt:
  keccak256(
      "FHE_comp" || op || operands... || ACL
      || block.chainid || blockhash(block.number-1) || block.timestamp
  )

unary:
  keccak256(
      "FHE_comp" || op || ct || ACL
      || block.chainid || blockhash(block.number-1) || block.timestamp
  )

randomness seed (via _generateSeed, used by fheRand and fheRandBounded):
  keccak256(
      "FHE_seed" || counterRand || ACL
      || block.chainid || blockhash(block.number-1) || block.timestamp
  )
```

Top 21 bytes form the random prefix; byte 21 is set to `0xff` (computation marker); the last 10 bytes carry `chainId | fheType | version`. See [./handles.md](./handles.md) for the full format, the rationale for the `blockhash` + `block.timestamp` inputs, and the opaque-handle rules.

## Validation order (per op)

1. Each input handle: `chainId == block.chainid`, recognised type, recognised version.
2. `ACL.isAllowed(handle, msg.sender)` for each input handle.
3. If binary and `scalarByte == 0x00`, validate `rhs` as well.
4. HCU cost: fits per-tx total, per-tx depth, and (if not whitelisted) per-block cap. See [./hcu-limits.md](./hcu-limits.md).
5. Generate deterministic output handle.
6. Auto-grant ACL: **transient** access (`ACL.allowTransient`) to `msg.sender` only — never `tx.origin`, never persistent. For state that survives the transaction, the contract must call `FHE.allowThis(handle)` itself.
7. Emit the op-specific `FHEEvent`.

## Events for the coprocessor

`FHEEvents.sol` emits one event per op. Each carries an indexed `caller` address, the operand handles and any scalar, and the output handle. Example: `FheAdd(address indexed caller, bytes32 lhs, bytes32 rhs, bytes1 scalarByte, bytes32 result)`. The full set is the standard FHE op names with `Fhe` prefix and mixed case (`FheAdd`, `FheMul`, `FheBitAnd`, `FheIfThenElse`, `FheSum`, `FheIsIn`, `FheRand`, `FheRandBounded`, `FheCast`, `FheTrivialEncrypt`, etc.). The coprocessor reconstructs the full computation graph from these events alone — no out-of-band signalling.
