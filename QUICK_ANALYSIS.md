# Quick Analysis Guide for Sequence Results

## One-Command Analysis

After collecting your SLURM results, analyze them with one simple command:

```bash
python analyze/analyze_sequence_results.py aggregated_results.csv
```

Plots are automatically saved in the same directory as your CSV file!

## What You Get

### 1. Console Output

```
Loaded 101 time points
  Aggregated across 20 seeds

Configuration:
  B = 240
  Method = immediately
  p = 0.600
  Mean alpha = 0.502

Final Results (at repetition 1,000):
  Time-avg fullness: 0.610877 +/- 0.000312
  Snapshot fullness: 0.610852 +/- 0.000362
  Change in last interval: 0.00000030
  Status: CONVERGED (change < 0.0001)

Comparison to theory:
  5/9 = 0.555556 (theoretical lower bound for p=0.6)
  Margin above bound: +0.055322 (+9.96%)
  OK: Result is safely above bound

Generating plots...
  Saved: analysis_convergence.png
  Saved: analysis_convergence_detail.png

>>> Analysis complete with plots!
```

### 2. Two Plots

**`analysis_convergence.png`** - Full convergence view
- Left panel: Time-averaged fullness over all repetitions
- Right panel: Snapshot fullness
- Shows mean ± 1 std across seeds
- See how quickly it converges

**`analysis_convergence_detail.png`** - Zoomed detail (last 20%)
- Fine-grained view of final convergence
- Confirms steady state reached
- Shows variance at equilibrium

## Complete Workflow

```bash
# 1. After SLURM jobs finish, collect results
cd runs/my_run_directory
python ../../leaf_splitting_sim_sequence_slurm.py collect \
    --results_dir results \
    --output aggregated.csv

# 2. Analyze and plot (one command!)
python ../../analyze/analyze_sequence_results.py aggregated.csv

# 3. View plots (automatically saved in your directory)
# analysis_convergence.png
# analysis_convergence_detail.png
```

Done! Plots are automatically saved in the same folder as your CSV.

## Interpreting Results

### Convergence Status

- **CONVERGED** (change < 0.0001): ✓ Results are reliable
- **Near convergence** (change < 0.001): ~ Probably okay
- **May need more repetitions**: ⚠ Increase repetitions and re-run

### Theoretical Comparisons

**For p=0.5:**
- Compares to ln(2) ≈ 0.693

**For p=0.6:**
- Compares to 5/9 ≈ 0.556 (theoretical lower bound)
- Shows margin above bound
- Indicates if result is near-adversarial

### Plot Interpretation

**Full convergence plot:**
- Rapid rise initially → transient phase
- Flattening → approaching steady state
- Flat line → converged
- Narrow error bands → stable across seeds

**Detail plot (last 20%):**
- Should be nearly flat if converged
- Small oscillations are normal
- Trend up/down → not fully converged

## Examples

### Example 1: Your r=1-240 sequence

```bash
cd runs/B240_immediately_r1-240_seq10k
python ../../analyze/analyze_sequence_results.py B240_immediately_r1-240_seq10k.csv
```

Result: 0.6109 ± 0.0003, converged, 9.96% above 5/9 bound ✓

Plots saved as:
- `analysis_convergence.png`
- `analysis_convergence_detail.png`

### Example 2: Hard case test

```bash
cd runs/B240_immediately_hardcase_p06_seq1M
# After collecting results...
python ../../analyze/analyze_sequence_results.py B240_hardcase_aggregated.csv
```

Expected: ~0.568, near 5/9 bound (near-adversarial)

Plots saved as:
- `analysis_convergence.png`
- `analysis_convergence_detail.png`

## Tips

1. **Plots auto-save** - no need to specify output location
2. **Check detail plot** - verifies true convergence
3. **Compare different runs** - put plots side by side
4. **Run from any directory** - plots save where your CSV is

---

**That's it!** One command after collect gives you complete analysis + publication-ready plots.

