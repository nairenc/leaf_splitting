# Hard Case Test: p=0.6 with Variable Batch Sizes (α ∈ {0.2, 0.4, 0.6, 0.8, 1.0})

## Motivation

**Theoretical Result:** For immediately split with p=0.6 and **fixed** r, the time-averaged fullness is guaranteed to be at least **5/9 ≈ 0.556**.

**Question:** Does this lower bound still hold when we use a **variable batch size sequence** instead of fixed r?

This run tests a challenging sequence that cycles through different α values to see if we can break below the 5/9 guarantee.

## Configuration

| Parameter | Value |
|-----------|-------|
| **Block capacity (B)** | 240 |
| **Method** | immediately |
| **Split ratio (p)** | 0.6 |
| **r_sequence** | [48, 96, 144, 192, 240] |
| **α sequence** | [0.2, 0.4, 0.6, 0.8, 1.0] |
| **Repetitions** | 1,000,000 |
| **Random seeds** | 20 |
| **Total tasks** | 20 (one per seed) |

## Sequence Design

The sequence cycles through 5 different batch sizes:

| Batch Size (r) | α = r/B | Workload Intensity |
|----------------|---------|-------------------|
| 48 | 0.2 | Light (20% of capacity) |
| 96 | 0.4 | Moderate (40% of capacity) |
| 144 | 0.6 | Heavy (60% of capacity) |
| 192 | 0.8 | Very Heavy (80% of capacity) |
| 240 | 1.0 | Maximum (100% of capacity) |

**Mean α:** 0.6 (average workload intensity)

This sequence is challenging because:
1. **High α values (0.8, 1.0)** force many splits
2. **Mixing different workloads** prevents steady-state optimization
3. **α=1.0** is particularly difficult for immediately split (~0.57 fullness)

## Computational Details

**Per task:**
- Sequence length: 5
- Repetitions: 1,000,000
- Insertions per cycle: 48 + 96 + 144 + 192 + 240 = 720
- **Total insertions: 720,000,000** (720 million)
- Estimated time: ~2-4 hours per task

**Total across all tasks:**
- Combined insertions: 14.4 billion
- Total tasks: 20

## Hypothesis

### Possible Outcomes

1. **Fullness ≥ 5/9 (≈ 0.556)**: Theory holds even with variable r
   - Strong evidence the 5/9 bound is fundamental for p=0.6
   - Variable workload doesn't break the guarantee

2. **Fullness < 5/9 (< 0.556)**: Theory doesn't extend to variable r
   - Need to refine theoretical analysis
   - Fixed r assumption was critical

3. **Fullness ≈ 5/9 boundary**: Sequence is "worst case"
   - Confirms 5/9 is tight
   - This particular sequence achieves the lower bound

## Expected Behavior by α Value

For fixed r at p=0.6 (from existing theory/results):

| α | Expected Fullness |
|---|------------------|
| 0.2 | ~0.60-0.65 |
| 0.4 | ~0.60-0.65 |
| 0.6 | ~0.65-0.70 |
| 0.8 | ~0.63-0.68 |
| 1.0 | ~0.57 (known bottleneck) |

**Weighted average:** ~(0.63+0.63+0.67+0.65+0.57)/5 ≈ **0.63**

But the **time-averaged** result might be different due to:
- Transient effects between different r values
- Non-equilibrium behavior when switching workloads
- Possible resonance effects

## Test Prediction

Based on the mixture and α=1.0 bottleneck:

**Predicted time-avg fullness: 0.58-0.63**

This would be **above** the 5/9 ≈ 0.556 threshold, suggesting the bound likely holds.

However, if there are unfavorable transient effects, we might see values closer to or even below 5/9.

## Files

- `sequence_sweep_config.json` - Configuration file
- `submit_slurm.sh` - SLURM submission script
- `results/` - Individual task outputs
- `B240_immediately_hardcase_p06_aggregated.csv` - Final results (after collection)

## Usage

### Submit Job

```bash
cd runs/B240_immediately_hardcase_p06_seq1M
sbatch submit_slurm.sh
```

### Monitor Progress

```bash
squeue -u $USER
tail -f /scratch/$USER/leaf_splitting/logs/B240_hardcase_*.out
ls results/result_*.csv | wc -l
```

### Collect Results

After all 20 tasks complete:

```bash
python ../../leaf_splitting_sim_sequence_slurm.py collect \
    --results_dir results \
    --output B240_immediately_hardcase_p06_aggregated.csv
```

### Check Result

```bash
# View the aggregated results
cat B240_immediately_hardcase_p06_aggregated.csv | column -t -s,

# Extract time-avg fullness
python -c "import pandas as pd; df = pd.read_csv('B240_immediately_hardcase_p06_aggregated.csv'); print(f'Time-avg fullness: {df[\"time_avg_fullness_mean\"].values[0]:.6f} ± {df[\"time_avg_fullness_std\"].values[0]:.6f}')"

# Compare to 5/9
python -c "print(f'5/9 threshold: {5/9:.6f}')"
```

## Comparison

Compare with fixed r runs:
- `B240_immediately_r1-240_p80_s20/` - Fixed r sweep (includes p=0.6 data)
- `B240_immediately_r1-360_p80_s20/` - Extended fixed r sweep

Look for:
- Does variable r give lower fullness than any fixed r at p=0.6?
- Is the result consistent with weighted average of fixed r results?

## Scientific Questions

1. **Does the 5/9 lower bound hold for variable batch sizes?**
2. **Is there an "adversarial" sequence that achieves exactly 5/9?**
3. **How does the result compare to the weighted average of fixed r values?**
4. **Are there transient effects when switching between different r values?**

## Notes

1. **1M repetitions** ensures we're at steady state despite varying r
2. **p=0.6 chosen** because it has known theoretical lower bound for fixed r
3. **Mean α = 0.6** matches a "moderate-heavy" workload
4. **Includes α=1.0** which is the worst case for immediately split

## Significance

If fullness < 5/9:
- **Major finding!** Theory needs revision
- Variable workload is harder than any fixed workload
- Need new analysis for time-varying batch sizes

If fullness ≈ 5/9:
- This sequence may be the "worst case"
- Confirms tightness of the bound

If fullness > 5/9:
- Theory likely extends to variable r
- Supports robustness of the 5/9 guarantee

## Created

November 10, 2025

## Status

Ready to submit! This is a **hypothesis-testing run** to check if theoretical guarantees extend beyond fixed batch sizes.

