# CSV Column Reference

## Minimal Column Output (Space-Optimized)

Both deferred_split and immediately_split now output **minimal essential columns** to save space.

### Deferred Split Columns

| Column | Type | Description |
|--------|------|-------------|
| `task_id` | int | SLURM task ID |
| `B` | int | Block capacity |
| `r` | int | Batch size |
| `alpha` | float | r/B ratio |
| `p` | float | Split ratio |
| `seed` | int | Random seed |
| `fullness` | float | **Primary metric** - average occupancy / B |

**Total: 7 columns**

### Immediately Split Columns

| Column | Type | Description |
|--------|------|-------------|
| `task_id` | int | SLURM task ID |
| `B` | int | Block capacity |
| `r` | int | Batch size |
| `alpha` | float | r/B ratio |
| `p` | float | Split ratio |
| `seed` | int | Random seed |
| `fullness` | float | Final fullness (average occupancy / B) |
| `time_avg_fullness` | float | Time-averaged fullness |

**Total: 8 columns**

### Key Difference

**Immediately split** includes one additional metric:
- `time_avg_fullness` - Time-averaged fullness throughout the simulation (vs final fullness)

**Deferred split** only has:
- `fullness` - Final average occupancy / B

## Why Minimal Columns?

**Removed redundant/computable columns:**
- ❌ `s` (same as r)
- ❌ `T` (= B - r)
- ❌ `p_min`, `p_max` (computable from alpha)
- ❌ `mu` (= fullness × B)
- ❌ `k_H`, `k_L`, `p_H_emp` (extra stats, rarely needed)
- ❌ `final_blocks`, `inserts`, `splits`, `moves` (operational details)
- ❌ `mode`, `rounding` (parameters, usually constant)

**Space savings:**
- Old deferred: ~15 columns → **New: 7 columns** (53% reduction)
- Old immediately: ~17 columns → **New: 8 columns** (53% reduction)
- For 96,000 records: saves ~500 KB to 1 MB per CSV file

## Analyze Script Compatibility

### `analyze_results.py` and `analyze_results_filtered.py`

Both scripts are now **fully compatible** with both deferred and immediately split CSVs.

**Required columns** (both methods have these):
- ✅ `B`, `r`, `alpha`, `p`, `seed`, `fullness`

**Optional columns** (handled gracefully if missing):
- `time_avg_fullness` - used if present

**Result:** Both CSV types work perfectly with all analyze scripts!

## Usage Examples

```bash
# Deferred split analysis
python analyze/analyze_results.py \
    --input runs/B120_r1-120_p40_s20_n100k/sweep_results.csv

# Immediately split analysis (same command!)
python analyze/analyze_results.py \
    --input runs/immediately_B120_r1-120_p40_s20/sweep_results.csv

# Filtered analysis works for both
python analyze/analyze_results_filtered.py \
    --input runs/test_immediately_B120/test_results.csv \
    --R 1 60
```

## File Size Comparison

**For 96,000 records:**
- Old format: ~15 MB (15 columns)
- New minimal format: ~7 MB (7-8 columns)
- **Space saved: ~8 MB (53% reduction)**

For large parameter sweeps, this significantly reduces storage and network transfer time!

## Migration

All new runs will automatically use minimal columns. Old CSVs will still load correctly in the updated analyze scripts (they only require the 6 core columns).

