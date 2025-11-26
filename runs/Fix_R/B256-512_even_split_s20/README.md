# Even Split Simulation: B256-512

Even split (p=0.5) simulation with multiple B values and auto-generated r values.

## Configuration

- **B values**: 256 to 512 (step=1, every value) = **257 B values**
- **Method**: deferred
- **Split ratio (p)**: 0.5 (even split)
- **Seeds**: 20
- **r values**: Auto-generated from 1 to B/2+1 for each B
  - B=256: r from 1 to 129 (129 values)
  - B=512: r from 1 to 257 (257 values, largest)
  - r values range from 129 to 257 depending on B

## Task Structure

- **Total tasks**: 5,140 (20 seeds × 257 B values)
- **Each task**: Runs all r values from 1 to B/2+1 for a specific (B, seed) combination
- **SLURM array**: `--array=0-5139`

## Insertion Strategy

- **Scale**: sqrt
- **Base insertions**: 100,000
- **Range**: 200,000 to 1,703,121 insertions
- **Formula**: `(sqrt(r) + 1) × 100,000`

## Running

```bash
cd runs/Fix_R/B256-512_even_split_s20
sbatch submit_slurm.sh
```

## Collecting Results

After all jobs complete:

```bash
python core/leaf_splitting_sim_even_split_slurm.py collect \
    --results_dir runs/Fix_R/B256-512_even_split_s20/results \
    --output runs/Fix_R/B256-512_even_split_s20/aggregated_results.csv
```

This will create an aggregated CSV with statistics (mean, std, min, max) for each (B, r) combination across all 20 seeds.

## Expected Output

- **Per-task results**: `results/result_*.csv` (100 files)
- **Aggregated results**: `aggregated_results.csv` (one row per (B, r) combination)
- **Columns**: B, r, alpha, p, fullness_mean, fullness_std, time_avg_fullness_mean, etc.

## Notes

- Each task runs a different number of r values depending on B
- Largest task (B=512) runs 257 r values, so allow sufficient time (6 hours)
- Memory: 4GB should be sufficient for all tasks
- **Large job**: This is a comprehensive sweep with 5,140 tasks. Consider:
  - Running in smaller batches if cluster has job limits
  - Monitoring resource usage
  - Allowing sufficient time for all tasks to complete

