# Analysis Scripts

This folder contains scripts for analyzing deferred split simulation results.

**Both scripts automatically detect and work with:**
- **Aggregated format (default)**: Contains pre-computed statistics with columns like `fullness_mean`, `fullness_std`, `n_seeds`
- **Per-seed format (legacy)**: Contains individual seed results with columns like `seed`, `fullness`, `time_avg_fullness`

**Note:** Results are aggregated by default during collection (see `collect` command below). The aggregation combines all random seeds for the same (r, p) combination, reducing file size by ~95%.

## Scripts

### 1. `analyze_results.py`
Generates comprehensive overview plots from sweep results.

**Figures generated:**
- Figure 1: Maximum fullness (over p) vs r/B with optimal p values
- Figure 2: Minimum fullness (over r) vs p with worst r values

**Usage:**
```bash
# Basic usage (saves figures in same directory as CSV)
python analyze_results.py --input path/to/sweep_results.csv

# From root directory (saves to runs/B120.../  )
python analyze/analyze_results.py --input runs/B120_r1-120_p40_s20_n100k/sweep_results.csv

# Specify custom save directory if needed
python analyze_results.py --input sweep_results.csv --save-dir custom_figures/
```

**Output files (examples):**
- `B256_r1-128_p0.01-0.50_maxp_fullness_vs_alpha.png`
- `B256_r1-128_p0.01-0.50_minr_fullness_vs_p.png`

---

### 2. `analyze_results_filtered.py`
Generates filtered plots for specific r or p values.

**Usage:**

**Filter by r/B ratios (fractional):**
```bash
# Plot fullness vs p for specific alpha values
python analyze_results_filtered.py --input sweep_results.csv --r 0.04 0.1 0.25 0.5
```

**Filter by exact r values (integer):**
```bash
# Plot fullness vs p for exact r values
python analyze_results_filtered.py --input sweep_results.csv --R 10 20 50 100
```

**Filter by p values:**
```bash
# Plot fullness vs r for specific p values
python analyze_results_filtered.py --input sweep_results.csv --p 0.3 0.4 0.5

# Or use uppercase P (same as lowercase p)
python analyze_results_filtered.py --input sweep_results.csv --P 0.3 0.4 0.5
```

**Examples:**
```bash
# Default (saves to same directory as CSV)
python analyze_results_filtered.py --input sweep_results.csv --r 0.1 0.2

# Custom save directory
python analyze_results_filtered.py --input sweep_results.csv --r 0.1 0.2 --save-dir custom_figures/
```

**Output files (examples):**
- `B256_r10_20_50_p0.01-0.50_fullness_vs_p.png` (when using --R)
- `B256_r25_64_128_p0.01-0.50_fullness_vs_p.png` (when using --r)
- `B256_r1-128_p0.30_0.40_fullness_vs_alpha.png` (when using --p)

---

## File Naming Convention

All generated figures follow this naming pattern:
- `B{block_size}_r{r_values}_p{p_values}_{description}.png`

Examples:
- `B256_r1-128_p0.01-0.50_maxp_fullness_vs_alpha.png`
  - B=256, r from 1 to 128, p from 0.01 to 0.50
  - Shows maximum fullness over all p values vs alpha (r/B)

- `B256_r10_20_50_p0.01-0.50_fullness_vs_p.png`
  - B=256, r values 10, 20, 50, p from 0.01 to 0.50
  - Shows fullness vs p for those specific r values

---

## Tips

1. **New runs:** Use the default `collect` behavior (automatic aggregation)
2. **Existing per-seed files:** Analysis scripts work with both formats - no changes needed!
3. **Use `analyze_results.py` first** to get an overview of all data
4. **Use `analyze_results_filtered.py`** when you need cleaner plots with specific r or p values
5. **Fractional r values (`--r`)** are more convenient for conceptual work (e.g., α=0.25)
6. **Integer r values (`--R`)** are better when you know exact values to plot
7. All figures are saved at **300 DPI** for publication quality
8. Figures are saved **in the same directory as the input CSV** by default (keeps each run's outputs together)
9. Both scripts support `--metric time_avg` (default, more stable) or `--metric final` (snapshot)

### Transition from Per-Seed to Aggregated Format

If you have existing per-seed result files and want to convert them to the new aggregated format:

```bash
# Convert existing per-seed file to aggregated format
python leaf_splitting_sim_slurm.py aggregate \
    --input runs/existing_run/results_perseed.csv \
    --output runs/existing_run/results.csv
    
# Analysis scripts work with both formats automatically
python analyze/analyze_results.py --input runs/existing_run/results.csv
```

---

## Collecting Simulation Results

After running SLURM jobs, collect individual task results into a single file. **Aggregation happens automatically by default:**

```bash
# Collect and aggregate results (default behavior - recommended)
python leaf_splitting_sim_slurm.py collect \
    --results_dir runs/B240_adaptive2_r1-240_p80_s20/results \
    --output runs/B240_adaptive2_r1-240_p80_s20/B240_adaptive2_r1-240_p80_s20_results.csv

# This automatically:
# - Collects all result_*.csv files from the results directory
# - Aggregates by (r, p) combination across all seeds
# - Computes mean, std, min, max for fullness metrics
# - Reduces file size by ~95% (e.g., 383K rows → 19K rows)

# Optional: Keep per-seed data (not recommended for large datasets)
python leaf_splitting_sim_slurm.py collect \
    --results_dir runs/B240_adaptive2_r1-240_p80_s20/results \
    --output runs/B240_adaptive2_r1-240_p80_s20/B240_adaptive2_r1-240_p80_s20_perseed.csv \
    --no-aggregate

# Legacy: Aggregate an existing per-seed file (if you have old data)
python leaf_splitting_sim_slurm.py aggregate \
    --input old_perseed_results.csv \
    --output aggregated_results.csv
```

## Examples from Project Root

```bash
# Analyze B120 deferred split (figures save to runs/B120_r1-120_p40_s20_n100k/)
python analyze/analyze_results.py \
    --input runs/B120_r1-120_p40_s20_n100k/sweep_results.csv

# Analyze B120 immediate split (figures save to runs/immediately_B120_r1-120_p40_s20/)
python analyze/analyze_results.py \
    --input runs/immediately_B120_r1-120_p40_s20/sweep_results.csv

# Create filtered plots (saves to same directory as CSV)
python analyze/analyze_results_filtered.py \
    --input runs/B120_r1-120_p40_s20_n100k/sweep_results.csv \
    --r 0.05 0.1 0.2 0.4

# Plot for test run
python analyze/analyze_results_filtered.py \
    --input runs/test_immediately_B120/test_results.csv \
    --R 1 60

# Use custom save directory if you want centralized figures
python analyze/analyze_results.py \
    --input runs/B120_r1-120_p40_s20_n100k/sweep_results.csv \
    --save-dir results_fig/
```

