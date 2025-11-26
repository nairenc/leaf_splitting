# Deferred Split Simulation Run: B240_deferred_r1-240_p40_s20

**Uses unified framework:** `leaf_splitting_sim_slurm.py` with `method='deferred'`

## Configuration

**Block and Batch Parameters:**
- Block size (B): 240
- Batch size range (r): 1 to 240 (240 values, step=1)
- Split ratio range (p): 0.11 to 0.5 (40 values)
- **Insertion strategy**: sqrt scaling
  - Formula: `total_insertions = (sqrt(r) + 1) × 100,000`
  - r=1: 200,000 insertions
  - r=16: 500,000 insertions
  - r=64: 900,000 insertions
  - r=120: 1,195,445 insertions
  - r=240: 1,649,138 insertions

**Rationale for sqrt scaling:**
- Balances computational load: small r → fewer insertions (slower per batch)
- Ensures all simulations reach steady state
- More fair comparison across different r values

**Experimental Design:**
- Number of seeds: 20
- Method: `deferred` (deferred split)
- Batching mode: `batch_by_r` (each task FIXES r, runs all p values)
- Total tasks: 4,800 (20 seeds × 240 r values)
- Total simulations: 192,000 (4,800 tasks × 40 p values)

**Derived Parameters:**
- α (alpha) range: r/B = 1/240 to 240/240 = 0.0042 to 1.0
- Threshold: splits when size ≥ B (at capacity)

## Task Distribution

Each SLURM array task handles:
- One (seed, r) combination
- Runs all 40 p values for that combination
- Total: 40 simulations per task

**Task mapping:**
- Task 0-239: seed 0, r values 1-240
- Task 240-479: seed 1, r values 1-240
- ...
- Task 4560-4799: seed 19, r values 1-240

## Files

- `sweep_config.json`: Configuration file with all parameters
- `submit_slurm.sh`: SLURM submission script
- `results/`: Directory for individual result CSV files
- `logs/`: Directory for SLURM output and error logs

## Running on SLURM

### Submit the job:
```bash
cd /home/nc1827/leaf_splitting/runs/B240_deferred_r1-240_p40_s20
sbatch submit_slurm.sh
```

### Monitor progress:
```bash
# Check job status
squeue -u nc1827

# Watch the latest log
tail -f /scratch/nc1827/leaf_splitting/logs/B240_sweep_*.out

# Count completed results
ls results/result_*.csv | wc -l
```

### After completion:

**Collect results:**
```bash
python ../../leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output B240_deferred_results.csv
```

**Analyze results:**
```bash
# Generate overview plots (saves figures in current directory)
python ../../analyze/analyze_results.py \
    --input B240_deferred_results.csv

# Generate filtered plots for specific r/B ratios (saves in current directory)
python ../../analyze/analyze_results_filtered.py \
    --input B240_deferred_results.csv \
    --r 0.1 0.2 0.4 0.8
```

## Expected Output

- 4,800 individual CSV files in `results/`
- Combined file: `B240_deferred_results.csv` (192,000 records)
- Analysis figures in current directory

## Computational Requirements

- Time per task: ~varies based on r value (larger r = more batches to process)
- Memory per task: 2GB
- Total wall time: depends on cluster load
- Estimated total CPU hours: ~4,800 tasks × avg_time
- Array size: 4,800 tasks

## Notes

- Uses `batch_by_r` mode for consistent task structure
- Each task runs all 40 p values for a fixed (seed, r) combination
- p range starts at 0.11 (avoiding very small p values)
- sqrt scaling ensures fair comparison across different r values
- Larger B=240 allows testing finer granularity of α = r/B ratios


