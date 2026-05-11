# FHEVM: HCU Limits

`HCULimit` budgets off-chain FHE compute. Every FHE op has an HCU cost from a `(operationType, fheType) → cost` table; `FHEVMExecutor` calls into `HCULimit` before returning each output handle.

## Caps

| Cap | Field | Scope | Notes |
|-----|-------|-------|-------|
| Per-tx total | `maxHCUPerTx` | One transaction | Sum of all op costs in the tx |
| Per-tx depth | `maxHCUDepthPerTx` | One transaction | Longest sequential dependency chain |
| Per-block global | `globalHCUCapPerBlock` | One block, non-whitelisted senders only | Resets when `block.number` advances |

Whitelisted accounts (via `blockHCUWhitelist`) skip the per-block cap but still respect per-tx caps. Whitelist write paths are `addToBlockHCUWhitelist` / `removeFromBlockHCUWhitelist`, both `onlyOwner`.

## Storage

```solidity
struct HCULimitStorage {
    uint48 globalHCUCapPerBlock;
    uint48 usedBlockHCU;
    uint48 lastSeenBlockNumber;
    uint48 maxHCUDepthPerTx;
    uint48 maxHCUPerTx;
    mapping(address => bool) blockHCUWhitelist;
}
```

`usedBlockHCU` is reset to 0 lazily when `block.number > lastSeenBlockNumber`.

## Validation order

```text
cost = hcuTable[op][fheType]

require(txHCUUsed  + cost <= maxHCUPerTx)
require(txHCUDepth + cost <= maxHCUDepthPerTx)
if (!whitelisted[msg.sender]):
    require(usedBlockHCU + cost <= globalHCUCapPerBlock)
    usedBlockHCU += cost
txHCUUsed += cost
```

Failure on any check reverts the operation.

## Events

```solidity
event GlobalHCUCapPerBlockUpdated(uint48 newCap);
event MaxHCUPerTxUpdated(uint48 newMax);
event MaxHCUDepthPerTxUpdated(uint48 newMax);
event BlockHCUWhitelistUpdated(address account, bool added);
```

## Cost intuition

Costs scale with type size and op type — `euint256` operations cost dramatically more HCU than `euint8`; multiplication and comparisons cost more than additions or bitwise ops. Use the smallest type that fits and prefer scalar operands. Concrete per-op cost tables live in the FHEVM docs and shift with releases — link out, don't hardcode.
