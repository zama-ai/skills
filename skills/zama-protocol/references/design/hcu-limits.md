# FHEVM: HCU Limits

`HCULimit` budgets off-chain FHE compute. Every FHE op has an HCU cost from a `(operationType, fheType) → cost` table; `FHEVMExecutor` calls into `HCULimit` before returning each output handle.

## Caps

| Cap | Field | Scope | Current mainnet/Sepolia deployment |
|-----|-------|-------|-----------------------------------|
| Per-tx total | `maxHCUPerTx` | One transaction (sum of all op costs) | `20_000_000` |
| Per-tx depth | `maxHCUDepthPerTx` | One transaction (longest sequential dependency chain) | `5_000_000` |
| Per-block global | `hcuPerBlock` | One block, non-whitelisted senders only | `281_474_976_710_655` (`type(uint48).max`) — effectively unbounded |

The block cap is set high enough today that the per-tx caps are the binding constraint in practice. Whitelisted accounts (via `blockHCUWhitelist`) skip the block cap entirely but still respect per-tx caps.

**Invariant enforced by the setters**: `hcuPerBlock ≥ maxHCUPerTx ≥ maxHCUDepthPerTx`. Setting a smaller `hcuPerBlock` than `maxHCUPerTx` reverts.

## Storage

```solidity
struct HCULimitStorage {
    uint48 hcuPerBlock;
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
    require(usedBlockHCU + cost <= hcuPerBlock)
    usedBlockHCU += cost
txHCUUsed += cost
```

Failure on any check reverts the operation.

## Admin surface (`onlyACLOwner`)

```solidity
function setHCUPerBlock(uint48 hcuPerBlock) external onlyACLOwner;
function setMaxHCUPerTx(uint48 maxHCUPerTx) external onlyACLOwner;
function setMaxHCUDepthPerTx(uint48 maxHCUDepthPerTx) external onlyACLOwner;

function addToBlockHCUWhitelist(address account) external onlyACLOwner;
function removeFromBlockHCUWhitelist(address account) external onlyACLOwner;
function isBlockHCUWhitelisted(address account) external view returns (bool);
```

All setters share `HCULimit`'s ownership with the ACL contract (`onlyACLOwner`, not the bare `onlyOwner`).

## Events

```solidity
event HCUPerBlockSet(uint48 hcuPerBlock);
event MaxHCUPerTxSet(uint48 maxHCUPerTx);
event MaxHCUDepthPerTxSet(uint48 maxHCUDepthPerTx);
event BlockHCUWhitelistAdded(address indexed account);
event BlockHCUWhitelistRemoved(address indexed account);
```

Add and remove use separate events — there's no single "updated" event with a boolean.

## Cost intuition

Costs scale with type size and op type — `euint256` operations cost dramatically more HCU than `euint8`; multiplication and comparisons cost more than additions or bitwise ops. Use the smallest type that fits and prefer scalar operands. Concrete per-op cost tables live in the FHEVM docs and shift with releases — link out, don't hardcode.
