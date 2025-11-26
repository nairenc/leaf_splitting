# Leaf Splitting Simulation - User Guide

Complete guide for running simulations, analyzing results, and understanding output data.

---

## Table of Contents

1. [Quick Commands](#quick-commands)
2. [Parameter Sweeps](#parameter-sweeps)
3. [Even Split Simulations](#even-split-simulations)
4. [SLURM Workflow](#slurm-workflow)
5. [Analysis](#analysis)
6. [Understanding Metrics](#understanding-metrics)
7. [CSV Data Format](#csv-data-format)

---

## Quick Commands

### Single Simulation (Local)

```python
from leaf_splitting_sim import simulate

result = simulate(
    B=120,                    # Block capacity
    r=60,                     # Batch size
    total_insertions=100000,  # Total keys to insert
    method='adaptive',        # Method: 'deferred', 'immediately', 'adaptive', 'adaptive2'
    p=0.3,                    # Split ratio
    seed=42                   # Random seed
)

print(f"Final fullness: {result['final_fullness']:.4f}")
print(f"Time-avg fullness: {result['time_avg_fullness']:.4f}")
```

### Generate SLURM Configuration

```bash
python leaf_splitting_sim_slurm.py config \
    --B 240 \
    --method adaptive \
    --r_min 1 --r_max 240 --r_step 1 \
    --p_min 0.11 --p_max 0.9 --p_count 80 \
    --seeds 20 \
    --insertion_scale sqrt \
    --batch_by_r \
    --output sweep_config.json
```

**Batching Modes:**

| Mode | Meaning | Tasks | Each Task Runs |
|------|---------|-------|----------------|
| `--batch_by_r` | **Fix r**, vary p | seeds × r_values | All p values |
| `--batch_by_p` | **Fix p**, vary r | seeds × p_values | All r values |
| Neither | Individual | seeds × r × p | Single combination |

**Insertion Scaling:**

| Strategy | Formula | Use Case |
|----------|---------|----------|
| `sqrt` | `(√r + 1) × base` | Balanced load (recommended) |
| `linear` | `r × base` | Linear scaling |
| `fixed` | `total_insertions` | Same for all r |

---

## Parameter Sweeps

### Typical Workflow

```bash
# 1. Create run directory
mkdir -p runs/B240_adaptive_test
cd runs/B240_adaptive_test

# 2. Generate configuration
python ../../leaf_splitting_sim_slurm.py config \
    --B 240 \
    --method adaptive \
    --r_min 1 --r_max 240 \
    --p_min 0.11 --p_max 0.9 --p_count 80 \
    --seeds 20 \
    --batch_by_r \
    --output sweep_config.json

# 3. Create SLURM submission script
cp ../../submit_slurm_template.sh submit_slurm.sh
# Edit submit_slurm.sh: set RUN_DIR, --array size, email

# 4. Submit to SLURM
sbatch submit_slurm.sh

# 5. Monitor
squeue -u $USER
tail -f /scratch/$USER/leaf_splitting/logs/*.out

# 6. Collect results (after completion)
python ../../leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output aggregated_results.csv

# 7. Analyze
python ../../analyze/analyze_results.py --input aggregated_results.csv
```

---

## Even Split Simulations

For comprehensive even split (p=0.5) studies with multiple B values, use `leaf_splitting_sim_even_split_slurm.py`. This script automatically generates r values from 1 to B/2+1 for each B, so you only need to specify B values, seeds, and splitting strategy.

### Quick Start

```bash
# Generate config - r values auto-generated from 1 to B/2+1
python core/leaf_splitting_sim_even_split_slurm.py config \
    --B-min 256 --B-max 512 --B-step 1 \
    --method deferred \
    --seeds 20 \
    --output even_split_config.json
```

**Key features:**
- **Auto-generated r values**: r from 1 to B/2+1 for each B (no need to specify r range)
- **Task structure**: Each task = (B, seed) combination, runs all r values
- **Perfect for**: Studying even split behavior across many B values

### Configuration Options

| Argument | Default | Description |
|----------|---------|-------------|
| `--B` | `[60, 120, 240, 480]` | List of B values (e.g., `--B 60 120 240`) |
| `--B-min` | - | Minimum B value (use with `--B-max`) |
| `--B-max` | - | Maximum B value |
| `--B-step` | 60 | Step for B values |
| `--method` | `deferred` | Split method: `deferred`, `immediately`, `adaptive`, `adaptive2`, `phased` |
| `--r-step` | 1 | Step for r values (r values are auto-generated from 1 to B/2+1) |
| `--p` | 0.5 | Split ratio (even split) |
| `--insertion_scale` | `sqrt` | `sqrt`, `linear`, or `fixed` |
| `--base_insertions` | 100000 | Base insertions for sqrt/linear scale |
| `--seeds` | 20 | Number of random seeds |
| `--output` | `even_split_config.json` | Output config filename |

### Example Workflow

```bash
# 1. Generate configuration
python core/leaf_splitting_sim_even_split_slurm.py config \
    --B-min 256 --B-max 512 --B-step 1 \
    --method deferred \
    --seeds 20 \
    --output even_split_config.json

# 2. Create run directory
mkdir -p runs/B256-512_even_split_s20
mv even_split_config.json runs/B256-512_even_split_s20/

# 3. Create submit_slurm.sh (update array size from config output)
# Example: --array=0-5139 for 5,140 tasks

# 4. Submit to SLURM
cd runs/B256-512_even_split_s20
sbatch submit_slurm.sh

# 5. Collect results
python core/leaf_splitting_sim_even_split_slurm.py collect \
    --results_dir results \
    --output aggregated_results.csv
```

### Task Structure

**Key difference from regular SLURM script:**

| Feature | Regular | Even Split |
|---------|---------|------------|
| Task structure | Task = (seed, r) or (seed, p) | Task = (B, seed) |
| Each task runs | All p values OR all r values | r values from 1 to B/2+1 |
| p values | Multiple | Fixed at 0.5 |
| B values | Single | Multiple |
| r values | Specified manually | Auto-generated per B (1 to B/2+1) |

**Example:**
- 4 B values [60, 120, 240, 480], 20 seeds
- Total tasks: 4 × 20 = **80 tasks**
- Each task runs different number of r values:
  - B=60: 31 r values (1 to 31)
  - B=120: 61 r values (1 to 61)
  - B=240: 121 r values (1 to 121)
  - B=480: 241 r values (1 to 241)

### Output Format

**Per-task results** (`result_*.csv`): One CSV per task with columns:
- `task_id`, `B`, `r`, `alpha`, `p`, `seed`, `fullness`, `time_avg_fullness`

**Aggregated results** (`aggregated_results.csv`): Statistics across seeds:
- `B`, `r`, `alpha`, `p`
- `fullness_mean`, `fullness_std`, `fullness_min`, `fullness_max`
- `time_avg_fullness_mean`, `time_avg_fullness_std`, etc.
- `n_seeds`: Number of seeds used

### Tips

1. **Memory**: Each task runs multiple r values, allocate 4-8GB
2. **Time**: Estimate based on number of r values per task. For B=512 (257 r values), allow 4-6 hours
3. **r values**: Automatically generated from 1 to B/2+1 - no need to specify manually!
4. **Large jobs**: For many B values (e.g., B=256-512 step=1 = 257 B values), you'll have many tasks. Check cluster limits.

---

## SLURM Workflow

### Submit Job

```bash
cd runs/your_run_name
sbatch submit_slurm.sh
```

### Monitor Jobs

```bash
squeue -u $USER              # Check job status
sacct -j JOBID               # Job details
tail -f logs/*.out           # View output
```

### Collect Results

```bash
# Aggregate across seeds (recommended)
python leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output final_results.csv

# Keep per-seed results (not recommended for large datasets)
python leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output all_seeds.csv \
    --no-aggregate
```

---

## Analysis

### Overview Plots

```bash
# Generate all plots with time-averaged fullness (default)
python analyze/analyze_results.py --input results.csv

# Use final fullness metric instead
python analyze/analyze_results.py --input results.csv --metric final
```

**Generated plots:**
- Fullness vs α (for max p)
- Fullness vs p (for min r)
- Fullness vs α and p (specific values if filtered)

### Filtered Analysis

```bash
# Specific r values (absolute)
python analyze/analyze_results_filtered.py \
    --input results.csv \
    --R 1 60 120

# Specific α = r/B ratios
python analyze/analyze_results_filtered.py \
    --input results.csv \
    --r 0.25 0.5 0.75 1.0

# Specific p values
python analyze/analyze_results_filtered.py \
    --input results.csv \
    --P 0.3 0.5 0.7

# Combine filters
python analyze/analyze_results_filtered.py \
    --input results.csv \
    --R 60 120 \
    --P 0.5 0.7 \
    --metric time_avg
```

---

## Understanding Metrics

### Two Fullness Metrics

The simulation computes two fullness metrics:

#### 1. Time-Averaged Fullness (Default)

**What it is:** Cumulative average of fullness over all insertions

**Formula:** `∑(total_keys × batch_size) / ∑(total_capacity × batch_size)`

**Properties:**
- ✅ More stable (lower variance across seeds)
- ✅ Better matches theoretical predictions
- ✅ Represents steady-state behavior
- ✅ **Recommended for method comparison**

#### 2. Final Fullness

**What it is:** Snapshot fullness at end of simulation

**Formula:** `final_keys / (B × final_blocks)`

**Properties:**
- Higher variance (stochastic fluctuations)
- May not be at steady state for finite runs
- Shows end-state of the system
- Useful for understanding transient behavior

### Example: r=1, p=0.5 (Theory: ln(2) = 0.693)

| Insertions | Final Fullness | Time-Avg Fullness |
|------------|----------------|-------------------|
| 100k       | 0.760          | 0.692             |
| 2M         | 0.682          | 0.697             |
| 16M        | 0.684          | 0.695             |
| Theory     | ~0.693 (limit) | 0.693             |

**Observation:** Time-averaged fullness (0.695) is closer to theory than final fullness (0.684).

### Usage

```bash
# Time-averaged (default, recommended)
python analyze/analyze_results.py --input results.csv

# Final fullness
python analyze/analyze_results.py --input results.csv --metric final
```

**Output files reflect the metric:**
- Time-averaged: `*_timeavg_fullness_*.png`
- Final: `*_final_fullness_*.png`

### Recommendation

**For scientific analysis:**
- Use `--metric time_avg` (default)
- More stable, matches theory better
- Represents steady-state behavior

**For end-state validation:**
- Use `--metric final`
- Shows final snapshot
- May have more variance

---

## CSV Data Format

### Aggregated Results (Default)

When you run `collect` with aggregation (default), you get statistics across seeds:

| Column | Type | Description |
|--------|------|-------------|
| `B` | int | Block capacity |
| `r` | int | Batch size |
| `alpha` | float | r/B ratio |
| `p` | float | Split ratio |
| `fullness_mean` | float | Mean final fullness across seeds |
| `fullness_std` | float | Standard deviation |
| `fullness_min` | float | Minimum value |
| `fullness_max` | float | Maximum value |
| `time_avg_fullness_mean` | float | Mean time-averaged fullness |
| `time_avg_fullness_std` | float | Standard deviation |
| `time_avg_fullness_min` | float | Minimum value |
| `time_avg_fullness_max` | float | Maximum value |
| `n_seeds` | int | Number of seeds aggregated |

### Per-Seed Results

When you run `collect --no-aggregate`, each row is one simulation run:

| Column | Type | Description |
|--------|------|-------------|
| `task_id` | int | SLURM task ID |
| `B` | int | Block capacity |
| `r` | int | Batch size |
| `alpha` | float | r/B ratio |
| `p` | float | Split ratio |
| `seed` | int | Random seed |
| `fullness` | float | Final fullness |
| `time_avg_fullness` | float | Time-averaged fullness |

### Why Minimal Columns?

We removed redundant/computable columns to save space:

**Removed:**
- ❌ `s` (same as r)
- ❌ `T` (= B - r)
- ❌ `mu` (= fullness × B)
- ❌ Operational details (splits, moves, etc.)

**Space savings:**
- Old: ~15 columns → New: 7-8 columns (53% reduction)
- For 96,000 records: saves ~8 MB per file

### Compatibility

Both analysis scripts work with both aggregated and per-seed formats:

```bash
# Works with aggregated results
python analyze/analyze_results.py --input aggregated_results.csv

# Works with per-seed results
python analyze/analyze_results.py --input all_seeds.csv
```

---

## Splitting Methods

### 1. Deferred Split

**Description:** Insert entire batch, then split if needed

**Best for:** α = 1.0, p ≈ 0.5 → achieves ~0.81 fullness!

**Key feature:** Can temporarily exceed capacity

### 2. Immediately Split

**Description:** Split incrementally during insertion

**Best for:** p > 0.6 at high α → up to ~0.69 fullness

**Key feature:** Never exceeds capacity

### 3. Adaptive Split

**Description:** Choose split point based on insertion location

**Best for:** p < 0.5 → up to 117% improvement over immediately!

**Key feature:** Keeps inserted elements in larger block

### 4. Adaptive2 Split

**Description:** Alternative adaptive strategy

**Key feature:** Different heuristic for split point selection

---

## Performance Tips

1. **Histogram optimization** makes simulations blazing fast:
   - 100k insertions: ~0.01-0.05s
   - Can run millions of insertions quickly

2. **Use batch_by_r** for parameter sweeps:
   - Fixes r, varies p per task
   - Better parallelization

3. **Use sqrt insertion scaling**:
   - Balanced computational load
   - Fair comparison across r values

4. **Aggregate results** to reduce file size:
   - Statistics across seeds
   - 53% smaller than per-seed files

---

## Common Issues

**Problem:** `KeyError: 'method'`  
**Solution:** Add `"method": "deferred"` to your config JSON

**Problem:** Results files not found  
**Solution:** Check `--results_dir` path, look for `result_*.csv`

**Problem:** Task ID out of range  
**Solution:** Check `--array` size matches config (e.g., 20 seeds → 0-19)

**Problem:** Jobs taking too long  
**Solution:** Reduce `--repetitions` or shorten simulation

---

## Quick Reference

### File Structure

```
leaf_splitting/
├── leaf_splitting_sim.py              # Core simulation
├── leaf_splitting_sim_slurm.py        # SLURM runner
├── USER_GUIDE.md                      # This file
├── TECHNICAL_DOCS.md                  # Algorithms & implementation
├── SEQUENCE_GUIDE.md                  # Sequence simulations
├── analyze/
│   ├── analyze_results.py             # Overview plots
│   └── analyze_results_filtered.py    # Filtered plots
└── runs/
    └── your_run_name/
        ├── sweep_config.json          # Configuration
        ├── submit_slurm.sh            # SLURM script
        ├── results/                   # Task outputs
        └── aggregated_results.csv     # Final results
```

### Method Selection Guide

| α Range | p Range | Best Method | Fullness |
|---------|---------|-------------|----------|
| 1.0     | 0.5     | Deferred    | ~0.81    |
| 0.8-1.0 | 0.2-0.4 | Adaptive    | ~0.70    |
| 0.8-1.0 | 0.6-0.8 | Immediately | ~0.69    |
| < 0.5   | 0.2-0.4 | Adaptive    | ~0.55    |

---

For technical details, algorithms, and bug fixes, see **TECHNICAL_DOCS.md**.

For sequence-based simulations, see **SEQUENCE_GUIDE.md**.

