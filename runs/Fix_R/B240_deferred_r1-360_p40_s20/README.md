# Deferred Split Simulation Run: B240_deferred_r1-360_p80_s20

**Uses unified framework:** `leaf_splitting_sim_slurm.py` with `method='deferred'`

## Configuration

**Block and Batch Parameters:**
- Block size (B): 240
- Batch size range (r): **1 to 360 (360 values, step=1)** ← Extended range!
- Split ratio range (p): 0.11 to 0.9 (80 values)
- **Insertion strategy**: sqrt scaling
  - Formula: `total_insertions = (sqrt(r) + 1) × 100,000`
  - r=1: 200,000 insertions
  - r=16: 500,000 insertions
  - r=64: 900,000 insertions
  - r=120: 1,195,445 insertions
  - r=240: 1,649,193 insertions
  - r=360: 1,996,644 insertions

**Rationale for extended r range:**
- α range: 1/240 to 360/240 = 0.0042 to 1.5
- Extends beyond α=1.0 to explore behavior when batch size exceeds block capacity
- At α>1.0, deferred method creates cascading splits
- 360 r values provides excellent granularity across the full spectrum

**Experimental Design:**
- Number of seeds: 20
- Method: `deferred` (insert batch, then split if needed)
- Batching mode: `batch_by_r` (each task FIXES r, runs all p values)
- Total tasks: **7,200** (20 seeds × 360 r values)
- Total simulations: **576,000** (7,200 tasks × 80 p values)

**Derived Parameters:**
- α (alpha) range: r/B = 1/240 to 360/240 = 0.0042 to 1.5
- Threshold: splits when size reaches B (after batch insertion)

## Task Distribution

Each SLURM array task handles:
- One (seed, r) combination
- Runs all 80 p values for that combination
- Total: 80 simulations per task

**Task mapping:**
- Task 0-359: seed 0, r values 1-360
- Task 360-719: seed 1, r values 1-360
- ...
- Task 6840-7199: seed 19, r values 1-360

## Files

- `sweep_config.json`: Configuration file with all parameters
- `submit_slurm.sh`: SLURM submission script
- `results/`: Directory for individual result CSV files
- `logs/`: Directory for SLURM output and error logs

## Running on SLURM

### Submit the job:
```bash
cd /home/nc1827/leaf_splitting/runs/B240_deferred_r1-360_p80_s20
sbatch submit_slurm.sh
```

### Monitor progress:
```bash
# Check job status
squeue -u nc1827

# Watch the latest log
tail -f /scratch/nc1827/leaf_splitting/logs/B240_def_r360_p80_sweep_*.out

# Count completed results
ls results/result_*.csv | wc -l
```

### After completion:

**Collect results:**
```bash
python ../../leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output B240_deferred_r1-360_p80_s20_results.csv
```

**Analyze results:**
```bash
# Generate overview plots (saves figures in current directory)
python ../../analyze/analyze_results.py \
    --input B240_deferred_r1-360_p80_s20_results.csv

# Generate filtered plots for specific r/B ratios (saves in current directory)
python ../../analyze/analyze_results_filtered.py \
    --input B240_deferred_r1-360_p80_s20_results.csv \
    --r 0.1 0.2 0.4 0.6 0.8 1.0 1.2 1.5
```

## Expected Output

- 7,200 individual CSV files in `results/`
- Combined file: `B240_deferred_r1-360_p80_s20_results.csv` (576,000 records)
- Analysis figures in current directory

## Computational Requirements

- Time per task: ~varies based on r value (larger r = more batches to process)
- Memory per task: 2GB
- Total wall time: depends on cluster load
- Estimated total CPU hours: ~7,200 tasks × avg_time
- Array size: 7,200 tasks

## Scientific Motivation

### Why extend r to 360 (α up to 1.5)?

1. **Beyond capacity**: Explore behavior when batch size exceeds block capacity
2. **Cascading splits**: At high α, deferred method creates multiple splits per insertion
3. **Complete picture**: Understand fullness behavior across full α spectrum
4. **Compare methods**: All 4 methods tested with same extended range

### Key Questions:
1. How does fullness change as α exceeds 1.0?
2. At what α does deferred method performance degrade?
3. How does optimal p change with α in the extended range?
4. What happens to cascading splits at very high α?

### Expected Findings:
- Fullness may decrease as α > 1.0 due to cascading splits
- Behavior at α < 1.0 should match previous B240 runs
- Deferred method may show different patterns than immediately/adaptive at α > 1.0

## Comparison Runs

This run complements:
- `B240_immediately_r1-360_p80_s20`: Same parameters, different method
- `B240_adaptive_r1-360_p80_s20`: Same parameters, adaptive split point
- `B240_adaptive2_r1-360_p80_s20`: Same parameters, symmetric adaptive split
- `B240_deferred_r1-240_p80_s20`: Same method, narrower r range

## Notes

- Uses sqrt scaling for fair comparison across different r values
- 80 p values provides high resolution for finding optima
- Extended to α=1.5 to explore behavior beyond block capacity
- Large job: 576,000 simulations total



