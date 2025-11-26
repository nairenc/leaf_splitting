# Sequence-Based Simulations - Complete Guide

Guide for running simulations with variable batch sizes (r_sequence) and deterministic insertion patterns.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start (Local)](#quick-start-local)
3. [Variable Batch Sizes (r_sequence)](#variable-batch-sizes-r_sequence)
4. [SLURM Execution](#slurm-execution)
5. [Command Reference](#command-reference)
6. [Python API](#python-api)

---

## Overview

The sequence simulation framework supports two types of simulations:

### 1. Variable Batch Sizes (r_sequence)
- **File:** `leaf_splitting_sim_sequence.py`
- **Purpose:** Test different batch sizes over time
- **Approach:** Histogram-based (efficient for large-scale)
- **Use case:** Statistical analysis with varying r values

### 2. Deterministic Insertion Patterns (Legacy)
- **File:** `test_sequence.py` (or custom scripts)
- **Purpose:** Test specific insertion patterns
- **Approach:** Track individual blocks
- **Use case:** Detailed step-by-step analysis

**This guide focuses on variable batch sizes (r_sequence), which is the primary tool.**

---

## Quick Start (Local)

### From Command Line

```bash
# Run with a simple sequence
python leaf_splitting_sim_sequence.py \
    --B 240 \
    --r-sequence 1 10 50 100 150 200 \
    --repetitions 1000 \
    --method immediately \
    --p 0.5 \
    --seed 42

# Use a config file
python leaf_splitting_sim_sequence.py --config my_config.json

# Generate example config
python leaf_splitting_sim_sequence.py --generate-config --output example.json
```

### From Python

```python
from leaf_splitting_sim_sequence import simulate_with_r_sequence

result = simulate_with_r_sequence(
    B=240,
    r_sequence=[1, 10, 50, 100, 150, 200],
    method='immediately',
    p=0.5,
    repetitions=1000,
    seed=42
)

print(f"Final fullness: {result['final_fullness']:.4f}")
print(f"Time-avg fullness: {result['time_avg_fullness']:.4f}")
print(f"Total insertions: {result['total_insertions']}")
print(f"Total splits: {result['total_splits']}")
```

---

## Variable Batch Sizes (r_sequence)

### What is r_sequence?

A **sequence of batch sizes** that the simulation cycles through:

```python
r_sequence = [1, 10, 50, 100, 150, 200]
repetitions = 1000
```

This means:
1. Insert batch of size 1
2. Insert batch of size 10
3. Insert batch of size 50
4. Insert batch of size 100
5. Insert batch of size 150
6. Insert batch of size 200
7. **Repeat** 1000 times

**Total insertions:** `(1+10+50+100+150+200) × 1000 = 511,000`

### Common Patterns

#### Testing burst patterns
```python
# Large bursts followed by small trickles
r_sequence = [100, 100, 100, 1, 1, 1]
repetitions = 500
```

#### Increasing workload
```python
# Gradually increasing batch sizes
r_sequence = [1, 10, 20, 40, 80, 160]
repetitions = 1000
```

#### Random-like (but reproducible)
```python
# Fixed sequence that appears random
r_sequence = [15, 87, 42, 123, 8, 91, 34]
repetitions = 2000
```

#### Testing specific α values
```python
# Cycle through different α = r/B values
B = 240
r_sequence = [
    int(0.1 * B),  # α = 0.1 → r = 24
    int(0.5 * B),  # α = 0.5 → r = 120
    int(0.9 * B),  # α = 0.9 → r = 216
]
repetitions = 1000
```

### Config File Format

```json
{
  "B": 240,
  "r_sequence": [1, 10, 50, 100, 150, 200],
  "repetitions": 1000,
  "method": "immediately",
  "p": 0.5,
  "rounding": "floor",
  "seed": 42
}
```

Save as `my_config.json` and run:
```bash
python leaf_splitting_sim_sequence.py --config my_config.json
```

---

## SLURM Execution

For running with multiple seeds in parallel on a SLURM cluster.

### Workflow

#### 1. Generate Configuration

```bash
python leaf_splitting_sim_sequence_slurm.py config \
    --B 240 \
    --method immediately \
    --p 0.5 \
    --r-sequence 1 10 50 100 150 200 \
    --repetitions 1000 \
    --seeds 20 \
    --output sequence_sweep_config.json
```

**Output:**
```
Configuration saved to sequence_sweep_config.json
Method: immediately
Block capacity (B): 240
Split ratio (p): 0.5
r_sequence: [1, 10, 50, 100, 150, 200]
Repetitions of sequence: 1000
Total tasks (seeds): 20

Each task will:
  - Use a different random seed
  - Run the same r_sequence 1000 times
  - Perform 511,000 total insertions

Use SLURM array job: #SBATCH --array=0-19
```

#### 2. Create Run Directory

```bash
mkdir -p runs/my_sequence_run
mv sequence_sweep_config.json runs/my_sequence_run/
```

#### 3. Create SLURM Submission Script

```bash
cp submit_slurm_sequence_template.sh runs/my_sequence_run/submit_slurm.sh
```

Edit `submit_slurm.sh`:
- Update `--array=0-19` to match number of seeds
- Update `RUN_DIR` path
- Update email address
- Adjust time/memory if needed

#### 4. Submit Job

```bash
cd runs/my_sequence_run
sbatch submit_slurm.sh
```

#### 5. Monitor Jobs

```bash
squeue -u $USER                          # Check status
tail -f /scratch/$USER/*/logs/*.out      # View output
```

#### 6. Collect Results

After all jobs complete:

```bash
python ../../leaf_splitting_sim_sequence_slurm.py collect \
    --results_dir results \
    --output aggregated_results.csv
```

This produces statistics across all seeds:
- Mean, std, min, max for fullness metrics
- One row summarizing all runs

### SLURM Configuration Options

| Argument | Default | Description |
|----------|---------|-------------|
| `--B` | 240 | Block capacity |
| `--method` | immediately | Split method |
| `--r-sequence` | (required) | Batch size sequence |
| `--p` | 0.5 | Split ratio |
| `--repetitions` | 1000 | Times to repeat sequence |
| `--rounding` | floor | Rounding method |
| `--seeds` | 20 | Number of random seeds (= tasks) |
| `--seeds_method` | seedsequence | Seed generation method |
| `--seeds_master` | 2025 | Master seed for reproducibility |
| `--output` | sequence_sweep_config.json | Config filename |

### SLURM Task Structure

**Key difference from regular SLURM script:**

| Feature | Regular | Sequence |
|---------|---------|----------|
| Batch size | Fixed `r` | Variable `r_sequence` |
| Task structure | Task = (seed, r, p) | Task = seed only |
| Number of tasks | seeds × r_values × p_values | seeds only |
| Each task runs | Single (r, p) combo | Full r_sequence |

**Example:**
- Regular with 20 seeds, 240 r values: 4,800 tasks
- Sequence with 20 seeds: **20 tasks** (much simpler!)

### Computational Cost

Each task runs `sum(r_sequence) × repetitions` insertions:

**Example:**
```python
r_sequence = [1, 10, 50, 100, 150, 200]  # sum = 511
repetitions = 1000
total_insertions = 511 × 1000 = 511,000
```

**Time estimate:** ~1-10 seconds per task (very efficient!)

Adjust `#SBATCH --time` accordingly:
- For 100k insertions: 5 minutes
- For 1M insertions: 15 minutes
- For 10M insertions: 1 hour

---

## Command Reference

### Local Execution

```bash
# Basic usage
python leaf_splitting_sim_sequence.py \
    --B 240 \
    --r-sequence 1 10 50 100 \
    --repetitions 1000 \
    --method immediately \
    --p 0.5 \
    --seed 42

# From config file
python leaf_splitting_sim_sequence.py --config my_config.json

# Generate example config
python leaf_splitting_sim_sequence.py --generate-config --output example.json

# Verbose output
python leaf_splitting_sim_sequence.py \
    --r-sequence 1 5 10 \
    --repetitions 10 \
    --method adaptive \
    --verbose

# Save results to JSON
python leaf_splitting_sim_sequence.py \
    --r-sequence 1 10 50 \
    --repetitions 100 \
    --output results.json
```

### SLURM Commands

```bash
# Generate config
python leaf_splitting_sim_sequence_slurm.py config \
    --B 240 \
    --method immediately \
    --r-sequence 1 10 50 100 \
    --repetitions 1000 \
    --seeds 20

# Run single task (called by SLURM)
python leaf_splitting_sim_sequence_slurm.py run \
    --config sequence_sweep_config.json \
    --task_id $SLURM_ARRAY_TASK_ID \
    --output_dir results

# Collect results (aggregate across seeds)
python leaf_splitting_sim_sequence_slurm.py collect \
    --results_dir results \
    --output aggregated_results.csv

# Collect without aggregation (keep per-seed)
python leaf_splitting_sim_sequence_slurm.py collect \
    --results_dir results \
    --output all_seeds.csv \
    --no-aggregate
```

---

## Python API

### Basic Usage

```python
from leaf_splitting_sim_sequence import simulate_with_r_sequence

result = simulate_with_r_sequence(
    B=240,
    r_sequence=[1, 10, 50, 100],
    method='immediately',
    p=0.5,
    repetitions=1000,
    seed=42
)
```

### Return Value

```python
{
    'method': str,              # Method used
    'B': int,                   # Block capacity
    'p': float,                 # Split ratio
    'r_sequence': list,         # Batch size sequence
    'repetitions': int,         # Times repeated
    'sequence_length': int,     # Length of sequence
    'total_insertions': int,    # Total keys inserted
    'total_splits': int,        # Number of splits
    'final_blocks': int,        # Final block count
    'final_fullness': float,    # Final fullness ratio
    'time_avg_fullness': float, # Time-averaged fullness
    'size_counts': dict,        # Histogram of block sizes
    'stats': Stats,             # Detailed statistics
}
```

### Configuration Management

```python
from leaf_splitting_sim_sequence import (
    read_config_from_file,
    write_config_to_file,
    write_results_to_file
)

# Read config
config = read_config_from_file('my_config.json')

# Run simulation
result = simulate_with_r_sequence(**config)

# Save results
write_results_to_file(result, 'output.json')
```

### Comparing Methods

```python
r_sequence = [1, 10, 50, 100]
methods = ['deferred', 'immediately', 'adaptive', 'adaptive2']

for method in methods:
    result = simulate_with_r_sequence(
        B=240,
        r_sequence=r_sequence,
        method=method,
        p=0.5,
        repetitions=1000,
        seed=42
    )
    print(f"{method:12s}: {result['time_avg_fullness']:.4f}")
```

### Comparing p Values

```python
r_sequence = [1, 10, 50, 100]
p_values = [0.3, 0.5, 0.7, 0.9]

for p in p_values:
    result = simulate_with_r_sequence(
        B=240,
        r_sequence=r_sequence,
        method='immediately',
        p=p,
        repetitions=1000,
        seed=42
    )
    print(f"p={p:.1f}: {result['time_avg_fullness']:.4f}")
```

---

## Output Data

### Individual Task CSV (Long Format)

Each SLURM task creates `results/result_NNNNNN.csv` with **one row per snapshot**:

| Column | Description |
|--------|-------------|
| `task_id` | SLURM task ID |
| `seed` | Random seed |
| `B` | Block capacity |
| `method` | Split method |
| `p` | Split ratio |
| `mean_alpha` | Mean α value |
| `total_insertions` | Total insertions |
| `total_splits` | Total splits |
| `split_rate` | Split rate |
| `final_blocks` | Number of blocks |
| `repetition` | Repetition/cycle number |
| `fullness` | Snapshot fullness at this point |
| `time_avg_fullness` | Time-averaged fullness up to this point |

**Example:**
```csv
task_id,seed,B,method,p,mean_alpha,...,repetition,fullness,time_avg_fullness
0,123,240,immediately,0.6,0.6,...,1,0.600,0.560
0,123,240,immediately,0.6,0.6,...,10001,0.567,0.567
0,123,240,immediately,0.6,0.6,...,20001,0.568,0.567
```

**For 1M repetitions with 100 snapshots:** 101 rows per task

### Aggregated Results CSV

After running `collect`, one row per repetition point with statistics:

| Column | Description |
|--------|-------------|
| `B` | Block capacity |
| `method` | Split method |
| `p` | Split ratio |
| `mean_alpha` | Mean α value |
| `repetition` | Repetition number |
| `fullness_mean` | Mean snapshot fullness across seeds |
| `fullness_std` | Standard deviation |
| `fullness_min` | Minimum value |
| `fullness_max` | Maximum value |
| `time_avg_fullness_mean` | Mean time-averaged fullness |
| `time_avg_fullness_std` | Standard deviation |
| `time_avg_fullness_min` | Minimum value |
| `time_avg_fullness_max` | Maximum value |
| `n_seeds` | Number of seeds aggregated |

**Example:**
```csv
B,method,p,mean_alpha,repetition,fullness_mean,fullness_std,...
240,immediately,0.6,0.6,1,0.601,0.003,...
240,immediately,0.6,0.6,10001,0.567,0.002,...
```

This **long-format** structure makes it easy to:
- Plot convergence over time
- Filter by specific repetition points
- Analyze time series data
- Use with any data analysis tool

---

## Tips and Best Practices

### 1. Sequence Design

**Good practices:**
- Keep sequence length reasonable (5-20 values)
- Use high repetitions for statistical stability (≥ 1000)
- Test specific patterns of interest (bursts, trends, cycles)

**Example patterns:**
```python
# Burst pattern
r_sequence = [100, 100, 100, 1, 1, 1]

# Ramp up
r_sequence = [1, 10, 20, 40, 80, 160]

# Cycle through α values
r_sequence = [int(a * B) for a in [0.1, 0.3, 0.5, 0.7, 0.9]]
```

### 2. Statistical Power

**More seeds = better statistics:**
- Minimum: 10 seeds
- Recommended: 20-50 seeds
- Trade-off with computational cost

### 3. Reproducibility

**Same config → identical results:**
```python
# Same seeds_master + seeds_method produces identical seeds
--seeds_master 2025
--seeds_method seedsequence
```

Seeds are saved in config and output for reproducibility.

### 4. Computational Efficiency

**Histogram-based approach is very efficient:**
- 500k insertions: ~1-5 seconds
- Memory: ~2GB sufficient for most cases
- No need for warm-up period

### 5. Memory Requirements

**Typical needs:**
- B=240, 1M insertions: ~1-2GB
- Increase if B or sequence very large

---

## Troubleshooting

**Problem:** "Task ID out of range"  
**Solution:** Check `--array` size matches number of seeds in config

**Problem:** Jobs taking too long  
**Solution:** Reduce `--repetitions` or shorten `--r-sequence`

**Problem:** Out of memory  
**Solution:** Increase `#SBATCH --mem` in submit script

**Problem:** Missing results files  
**Solution:** Check error logs in `/scratch/.../logs/` directory

---

## Comparison: Regular vs Sequence

| Feature | Regular Simulation | Sequence Simulation |
|---------|-------------------|---------------------|
| **Batch size** | Fixed r | Variable r_sequence |
| **Input** | r_list, p_list | Single r_sequence, single p |
| **SLURM tasks** | seeds × r_values × p_values | seeds only |
| **Use case** | Parameter sweeps | Time-varying patterns |
| **Example tasks** | 4,800 (20 seeds × 240 r) | 20 (seeds only) |

---

## Examples

### Example 1: Burst Testing

```bash
python leaf_splitting_sim_sequence_slurm.py config \
    --B 240 \
    --method immediately \
    --r-sequence 100 100 100 1 1 1 \
    --repetitions 500 \
    --seeds 20
```

Tests: Large bursts (100) followed by trickles (1)

### Example 2: Increasing Load

```bash
python leaf_splitting_sim_sequence_slurm.py config \
    --B 240 \
    --method adaptive \
    --r-sequence 1 10 20 40 80 160 \
    --repetitions 1000 \
    --seeds 20
```

Tests: Gradually increasing batch sizes

### Example 3: Alpha Cycling

```python
# Python script
B = 240
alphas = [0.1, 0.3, 0.5, 0.7, 0.9]
r_sequence = [int(a * B) for a in alphas]
# r_sequence = [24, 72, 120, 168, 216]

result = simulate_with_r_sequence(
    B=B,
    r_sequence=r_sequence,
    method='immediately',
    p=0.5,
    repetitions=2000,
    seed=42
)
```

Tests: Different α values in one run

---

## Analyzing Results

After collecting results, analyze and visualize convergence:

```bash
python analyze/analyze_sequence_results.py aggregated_results.csv
```

**What this does:**
1. Prints detailed statistics (fullness, convergence, theoretical comparisons)
2. Auto-saves `analysis_convergence.png` - Full convergence plot
3. Auto-saves `analysis_convergence_detail.png` - Zoomed detail (last 20%)

Plots are automatically saved in the same directory as your CSV file!

**Example output:**
```
📊 Loaded aggregated data: 101 time points
   Aggregated across 20 seeds

⚙️  Configuration: B=240, method=immediately, p=0.600, Mean α=0.600

📈 Results:
   Time-avg fullness: 0.567787 ± 0.002234
   ✓ Converged (change < 0.0001)

🎯 Comparison to theory:
   5/9 = 0.555556 (theoretical lower bound for p=0.6)
   Margin above bound: +0.012231 (+2.20%)
```

See **[QUICK_ANALYSIS.md](QUICK_ANALYSIS.md)** for complete workflow and examples.

## See Also

- **USER_GUIDE.md** - General simulation guide
- **QUICK_ANALYSIS.md** - Analysis and visualization workflow
- **TECHNICAL_DOCS.md** - Algorithms and implementation
- **README.md** - Project overview

---

**Created:** November 5, 2025  
**Updated:** November 10, 2025

