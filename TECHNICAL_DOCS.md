# Comprehensive Documentation

Complete technical documentation for the leaf splitting simulation framework.

---

## Table of Contents

1. [Simulation Methods](#simulation-methods)
2. [Algorithms](#algorithms)
3. [Bug Fixes and Updates](#bug-fixes-and-updates)
4. [Performance Analysis](#performance-analysis)
5. [Implementation Details](#implementation-details)
6. [Migration Guide](#migration-guide)

---

## Simulation Methods

### 1. Deferred Split

**Description**: Inserts all r elements of a batch into a block, then splits if the block size reaches or exceeds capacity B.

**Algorithm**:
```
1. Insert entire batch of r keys into block
2. If block size >= B:
   - Split at position p*size
   - Cascade if resulting blocks >= B
3. Otherwise, no split
```

**Key Features**:
- Can temporarily exceed capacity before splitting
- Supports cascading splits (added Oct 17, 2025)
- Best for α = r/B = 1.0 with p ≈ 0.5

**Performance**:
- Maximum fullness: ~0.81 at (α=1.0, p=0.5)
- Good for high α scenarios

**Cascading Split Fix** (Oct 17, 2025):
- **Bug**: Previously only split once, even if resulting blocks exceeded B
- **Impact**: For r=108, B=120, p=0.1, would create block of size 206 > B
- **Fix**: Now recursively splits until all blocks < B

---

### 2. Immediately Split

**Description**: Inserts elements incrementally, splitting immediately when block reaches capacity B during insertion.

**Algorithm**:
```
For each element in batch:
  1. If block has space: insert element
  2. If block reaches capacity B: split at p*B
  3. Continue insertion in appropriate child
```

**Key Features**:
- Never exceeds capacity
- Splits during insertion (not after)
- Natural cascading through iteration

**Performance**:
- Maximum fullness: ~0.69 at (α=0.9, p=0.7)
- Best for p > 0.6
- Limited to ~0.57 at α=1.0

---

### 3. Adaptive Split (NEW - Oct 17, 2025)

**Description**: Enhancement of immediately method that chooses split point (p or 1-p) based on insertion location to keep inserted elements in the larger block.

**Algorithm**:
```
When block reaches capacity B during insertion at position t:
  insert_end_pos = t + elements_inserted_so_far
  
  if insert_end_pos < p*B:
    split at p → blocks [p*B, (1-p)*B]
  else:
    split at (1-p) → blocks [(1-p)*B, p*B]
```

**Key Insight**: By choosing the split point, newly inserted elements stay in the larger block, improving packing density.

**Performance**:

*When p < 0.5* (HUGE improvements):
- (α=0.75, p=0.2): +117% vs immediately (0.345 → 0.750)
- (α=0.90, p=0.2): +114% vs immediately (0.321 → 0.686)
- (α=1.00, p=0.2): +83% vs immediately (0.301 → 0.551)
- (α=0.50, p=0.3): +17% vs immediately (0.480 → 0.562)

*When p = 0.5*: Identical to immediately (symmetric splits)

*When p > 0.5* (some degradation):
- (α=0.90, p=0.8): -31% vs immediately (0.688 → 0.478)
- (α=0.75, p=0.7): -26% vs immediately (0.735 → 0.541)

**Recommendation**: Use adaptive for p < 0.5, immediately for p > 0.5

---

## Bug Fixes and Updates

### 1. Cascading Splits Bug (Fixed Oct 17, 2025)

**Issue**: Deferred method didn't handle cascading splits

**Symptoms**:
- For r=108, B=120, all p values (0.11-0.5) gave identical fullness=0.9
- Blocks larger than B existed in the system

**Example**:
```
Block 120 + batch 108 = 228
With p=0.1: Should split 228 → [22, 206] → [22, 20, 186] (cascade!)
Bug: Only split once to [22, 206], leaving block 206 > B
```

**Fix**: Implemented recursive splitting:
```python
def insert_deferred(block_size, batch_size):
    new_size = block_size + batch_size
    if new_size < B:
        return [new_size], 0
    
    # Cascade split until all blocks < B
    blocks_to_split = [new_size]
    resulting_blocks = []
    num_splits = 0
    
    while blocks_to_split:
        current_size = blocks_to_split.pop(0)
        if current_size < B:
            resulting_blocks.append(current_size)
        else:
            left, right = split_size(current_size)
            num_splits += 1
            if left >= B:
                blocks_to_split.append(left)
            else:
                resulting_blocks.append(left)
            if right >= B:
                blocks_to_split.append(right)
            else:
                resulting_blocks.append(right)
    
    return resulting_blocks, num_splits
```

**Impact**: All deferred method results before Oct 17, 2025 are INVALID and must be re-run.

---

### 2. Defensive Coding Update (Oct 17, 2025)

**Issue**: Silent fallback to immediately method when unknown method specified

**Problem**:
```python
# Old code
if method == 'deferred':
    # ...
elif method == 'adaptive':
    # ...
else:  # Dangerous! Silent fallback
    # ... use immediately
```

If method='adaptiv' (typo) or code is outdated, would silently use immediately method.

**Fix**: Explicit validation:
```python
if method == 'deferred':
    new_blocks, num_splits = insert_deferred(old_size, r)
elif method == 'adaptive':
    new_blocks, num_splits = insert_adaptive(old_size, insert_pos, r)
elif method == 'immediately':
    new_blocks, num_splits = insert_immediately(old_size, insert_pos, r)
else:
    raise ValueError(f"Unknown method '{method}'. Must be 'deferred', 'immediately', or 'adaptive'.")
```

**Benefits**:
- Catches typos immediately
- Fails fast with clear error message
- No silent bugs

---

## Performance Analysis

### Method Comparison by Region

| α Range | p Range | Best Method | Fullness | Notes |
|---------|---------|-------------|----------|-------|
| 1.0     | 0.5     | Deferred    | ~0.81    | Absolute best |
| 0.8-1.0 | 0.2-0.4 | Adaptive    | ~0.70    | Much better than immediately |
| 0.8-1.0 | 0.6-0.8 | Immediately | ~0.69    | Best for high p |
| 0.5     | 0.5     | All same    | ~0.50    | Tie at α=0.5, p=0.5 |
| < 0.5   | 0.2-0.4 | Adaptive    | ~0.55    | Consistent advantage |

### Key Findings

1. **Deferred dominates at α=1.0, p=0.5**
   - Achieves ~0.81 fullness (41% better than immediately)
   - Temporary oversizing enables better packing

2. **Adaptive best for p < 0.5**
   - Up to 117% improvement over immediately
   - Keeps elements in larger blocks

3. **Immediately best for p > 0.6**
   - Consistent performance at high p
   - Adaptive degrades beyond p=0.6

4. **α=1.0 is special**
   - Immediately limited to ~0.57 fullness
   - Deferred achieves ~0.81
   - Every insertion forces splits

---

## Implementation Details

### Histogram-Based Simulation

Instead of maintaining individual blocks, we use a **size histogram**:

```python
size_counts = {
    60: 100,  # 100 blocks of size 60
    80: 50,   # 50 blocks of size 80
    # etc.
}
```

**Advantages**:
- Memory efficient: O(distinct sizes) instead of O(blocks)
- Fast updates: O(1) per size change
- Enables millions of blocks

**Sampling**: Pick block with probability ∝ size (models uniform key distribution)

### Insertion Scaling

**Square root scaling** (default):
```
total_insertions = (√r + 1) × 100,000
```

**Rationale**:
- Small r → fewer insertions (slower per batch, needs fewer to reach steady state)
- Large r → more insertions (faster per batch, needs more to reach steady state)
- Fair comparison across different r values

**Examples**:
- r=1: 200,000 insertions
- r=64: 900,000 insertions  
- r=240: 1,649,193 insertions

---

## Migration Guide

### From Old to Unified Framework

The project was unified on [date] to support multiple methods in one codebase.

**Old structure**:
- `leaf_splitting_deferred.py`
- `leaf_splitting_immediately.py`

**New structure**:
- `leaf_splitting_sim.py` (all methods)
- Method selected via `method` parameter

**Migration**:
```python
# Old
from leaf_splitting_deferred import simulate as simulate_deferred
result = simulate_deferred(B, r, n, p)

# New
from leaf_splitting_sim import simulate
result = simulate(B, r, n, method='deferred', p=p)
```

**Config files**: Now include `"method": "deferred"` field

---

## Testing and Validation

### Unit Tests

```python
# Test all three methods
for method in ['deferred', 'immediately', 'adaptive']:
    result = simulate(B=120, r=60, total_insertions=60000, 
                     method=method, p=0.3, seed=42)
    assert result['final_fullness'] > 0
    assert result['final_blocks'] > 0
```

### Validation

Compare with analytical results:
- α=0.5, p=0.5: All methods should give fullness ≈ 0.5
- Check that no blocks exceed capacity B
- Verify split counts are reasonable

---

## References

See individual run README files in `runs/` directory for specific configurations and results.

See `QUICK_REFERENCE.md` for common commands.

See `CSV_COLUMN_REFERENCE.md` for output data format.

---

**Last Updated**: October 17, 2025

