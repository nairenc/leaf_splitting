# B240 Immediately Split - Full r_sequence (1-240) with 10k Repetitions

## Overview

This run simulates the **immediately split** method with a complete sequence of batch sizes from r=1 to r=240, repeated 10,000 times.

## Configuration

| Parameter | Value |
|-----------|-------|
| **Block capacity (B)** | 240 |
| **Method** | immediately |
| **Split ratio (p)** | 0.5 |
| **r_sequence** | [1, 2, 3, ..., 240] (all 240 values) |
| **Repetitions** | 10,000 |
| **Random seeds** | 20 |
| **Total tasks** | 20 (one per seed) |

## Computational Details

**Per task:**
- Sequence length: 240 values
- Repetitions: 10,000
- **Total insertions: 289,200,000** (289.2 million)
- Estimated time: ~1-2 hours per task

**Total across all tasks:**
- Total insertions: 5.78 billion
- Total tasks: 20

## Sequence Statistics

| Metric | Value |
|--------|-------|
| Mean r | 120.5 |
| Mean α (r/B) | 0.5021 |
| Min r | 1 |
| Max r | 240 |

This sequence covers the full range of α values from very small (α ≈ 0.004 for r=1) to maximum (α = 1.0 for r=240).

## Purpose

This simulation tests the **immediately split** method across:
- **All possible batch sizes** (r = 1 to 240)
- **Very high repetition count** (10,000) for statistical stability
- **Fixed split ratio** (p = 0.5) for baseline comparison

Expected to reveal:
- How immediately split behaves across the full α spectrum
- Steady-state fullness for each α value
- Overall time-averaged behavior with varying workloads

## Files

- `sequence_sweep_config.json` - Configuration file
- `submit_slurm.sh` - SLURM submission script
- `results/` - Individual task outputs (result_000000.csv to result_000019.csv)
- `aggregated_results.csv` - Final aggregated results (after collection)

## Usage

### Submit Job

```bash
cd runs/B240_immediately_r1-240_seq10k
sbatch submit_slurm.sh
```

### Monitor Progress

```bash
# Check job status
squeue -u $USER

# View output
tail -f /scratch/$USER/leaf_splitting/logs/B240_seq_*.out

# Count completed tasks
ls results/result_*.csv | wc -l
```

### Collect Results

After all 20 tasks complete:

```bash
python ../../leaf_splitting_sim_sequence_slurm.py collect \
    --results_dir results \
    --output B240_immediately_r1-240_seq10k_aggregated.csv
```

This will aggregate results across all 20 seeds, computing mean, std, min, max for fullness metrics.

### Keep Per-Seed Results (Optional)

```bash
python ../../leaf_splitting_sim_sequence_slurm.py collect \
    --results_dir results \
    --output B240_immediately_r1-240_seq10k_all_seeds.csv \
    --no-aggregate
```

## Expected Results

Based on immediately split behavior:

| α Range | Expected Time-Avg Fullness |
|---------|---------------------------|
| 0.0-0.2 | ~0.50-0.55 |
| 0.2-0.5 | ~0.50-0.60 |
| 0.5-0.8 | ~0.55-0.65 |
| 0.8-1.0 | ~0.55-0.57 |

The **time-averaged fullness** across the full sequence should be around **0.55-0.60** with p=0.5.

## Comparison

This run complements:
- `B240_immediately_r1-240_p80_s20/` - Fixed r parameter sweep (different approach)
- `B240_deferred_r1-240_p40_s20/` - Deferred method comparison
- `B240_adaptive_r1-240_p80_s20/` - Adaptive method comparison

**Key difference:** This uses a **sequence** (varying r over time) rather than fixed r per simulation.

## Notes

1. **High insertion count:** 289M insertions per task is large but efficient with histogram method
2. **Memory usage:** 4GB should be sufficient
3. **Time estimate:** ~1-2 hours per task (adjust if needed)
4. **p=0.5 baseline:** Using p=0.5 for fair comparison with theoretical predictions

## Created

November 10, 2025

