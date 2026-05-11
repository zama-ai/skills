# FHEVM: FHE Operations and Symbolic Execution

`FHEVMExecutor` is the on-chain symbolic execution engine. It does **no** cryptographic work — it validates inputs, charges HCU, generates a deterministic output handle, and emits an event. The coprocessor's `host-listener` picks the event up and runs the actual TFHE op off-chain. The handle is usable immediately by subsequent FHE calls; only decryption waits for the coprocessor.

## Operations

### Binary (`(bytes32 lhs, bytes32 rhs, bytes1 scalarByte)`)

```text
fheAdd · fheSub · fheMul · fheDiv · fheRem      arithmetic
fheBitAnd · fheBitOr · fheBitXor                bitwise
fheShl · fheShr · fheRotl · fheRotr             shift / rotate
fheEq · fheNe · fheLt · fheLe · fheGt · fheGe   comparison → ebool
fheMin · fheMax                                 aggregation
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
function cast(bytes32 ct, FheType toType)               returns (bytes32);
function trivialEncrypt(uint256 pt, FheType toType)     returns (bytes32);
function verifyInput(bytes32 inputHandle, bytes inputProof) returns (bytes32);
```

`trivialEncrypt` is visible to anyone reading the chain — for constants and defaults only.

### Randomness

```solidity
function fheRand(FheType randType)                          returns (bytes32);
function fheRandBounded(uint256 upperBound, FheType randType) returns (bytes32);
```

`upperBound` must be a power of 2 (e.g. `128`, not `100`).

### Aggregates

```solidity
function fheSum(bytes32[] values, FheType resultType) returns (bytes32);
function fheIsIn(bytes32 value, bytes32[] values, FheType valueType) returns (bytes32); // result is ebool
```

## Handle generation

```text
binary:    keccak256("FHE_comp" || op || lhs || rhs || scalarByte || acl || chainId || blockhash(block.number-1))
unary:     keccak256("FHE_comp" || op || ct  || acl || chainId || blockhash(block.number-1))
ternary:   keccak256("FHE_comp" || op || lhs || mid || rhs || acl || chainId || blockhash(block.number-1))
rand:      keccak256("FHE_seed" || counterRand++ || fheType)        # no blockhash
trivial:   keccak256("FHE_comp" || TRIVIAL_ENCRYPT_OPCODE || plaintext || fheType)
```

Top 21 bytes form the random prefix; the last 11 bytes are overwritten with `chainId | fheType | version`. See [./handles.md](./handles.md) for the full format, the rationale for the `blockhash` input, and the opaque-handle rules.

## Validation order (per op)

1. Each input handle: `chainId == block.chainid`, recognised type, recognised version.
2. `ACL.isAllowed(handle, msg.sender)` for each input handle.
3. If binary and `scalarByte == 0x00`, validate `rhs` as well.
4. HCU cost: fits per-tx total, per-tx depth, and (if not whitelisted) per-block cap. See [./hcu-limits.md](./hcu-limits.md).
5. Generate deterministic output handle.
6. Auto-grant ACL: persistent allow for `msg.sender` and `tx.origin` on the output (does **not** propagate to next tx — call `FHE.allowThis()` for that).
7. Emit the op-specific `FHEEvent`.

## Events for the coprocessor

`FHEEvents.sol` emits one event per op. Each carries the operation type, input handles, scalar value (if any), output handle, caller context, and block number. The coprocessor reconstructs the full computation graph from these events alone — no out-of-band signalling.
