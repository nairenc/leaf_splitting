# Adaptive Split Simulation Run: B240_adaptive_r1-360_p80_s20

**Uses unified framework:** `leaf_splitting_sim_slurm.py` with `method='adaptive'`

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
- At high α, adaptive method dynamically chooses split point based on insertion location
- 360 r values provides excellent granularity across the full spectrum

**Adaptive Split Strategy:**
- If insertion location < p×B: split at position p
- If insertion location ≥ p×B: split at position (1-p)
- Goal: Keep inserted elements in larger resulting block

**Experimental Design:**
- Number of seeds: 20
- Method: `adaptive` (adaptive split point during insertion)
- Batching mode: `batch_by_r` (each task FIXES r, runs all p values)
- Total tasks: **7,200** (20 seeds × 360 r values)
- Total simulations: **576,000** (7,200 tasks × 80 p values)

**Derived Parameters:**
- α (alpha) range: r/B = 1/240 to 360/240 = 0.0042 to 1.5
- Split point: dynamically chosen based on insertion location

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
cd /home/nc1827/leaf_splitting/runs/B240_adaptive_r1-360_p80_s20
sbatch submit_slurm.sh
```

### Monitor progress:
```bash
# Check job status
squeue -u nc1827

# Watch the latest log
tail -f /scratch/nc1827/leaf_splitting/logs/B240_adp_r360_p80_sweep_*.out

# Count completed results
ls results/result_*.csv | wc -l
```

### After completion:

**Collect results:**
```bash
python ../../leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output B240_adaptive_r1-360_p80_s20_results.csv
```

**Analyze results:**
```bash
# Generate overview plots (saves figures in current directory)
python ../../analyze/analyze_results.py \
    --input B240_adaptive_r1-360_p80_s20_results.csv

# Generate filtered plots for specific r/B ratios (saves in current directory)
python ../../analyze/analyze_results_filtered.py \
    --input B240_adaptive_r1-360_p80_s20_results.csv \
    --r 0.1 0.2 0.4 0.6 0.8 1.0 1.2 1.5
```

## Expected Output

- 7,200 individual CSV files in `results/`
- Combined file: `B240_adaptive_r1-360_p80_s20_results.csv` (576,000 records)
- Analysis figures in current directory

## Computational Requirements

- Time per task: ~varies based on r value (larger r = more batches to process)
- Memory per task: 2GB
- Total wall time: depends on cluster load
- Estimated total CPU hours: ~7,200 tasks × avg_time
- Array size: 7,200 tasks

## Scientific Motivation

### Why adaptive splitting?

The adaptive method aims to improve upon fixed split points by:
1. **Location-aware**: Adjusts split point based on where insertion occurs
2. **Minimize fragmentation**: Keeps inserted elements in larger block
3. **Better fullness**: Potentially achieves higher fullness than fixed p

### Why extend r to 360 (α up to 1.5)?

1. **Beyond capacity**: Explore how adaptive strategy performs when batch exceeds block capacity
2. **Dynamic advantage**: At high α, adaptive split choice may provide significant benefits
3. **Compare to fixed**: How does adaptive compare to immediately method at high α?
4. **Complete spectrum**: Understand adaptive behavior across full range

### Key Questions:
1. Does adaptive method achieve higher fullness than immediately at high α?
2. How does optimal p for adaptive compare to immediately?
3. Does the adaptive split choice provide more benefit at certain α values?
4. What happens to adaptive performance as α exceeds 1.0?

### Expected Findings:
- Adaptive method may achieve higher fullness than immediately method
- Optimal p may differ from immediately method
- Benefits of adaptive splitting may be most pronounced at intermediate α
- Performance at α > 1.0 will reveal robustness of adaptive strategy

## Comparison Runs

This run complements:
- `B240_immediately_r1-360_p80_s20`: Fixed split point at p
- `B240_deferred_r1-360_p80_s20`: Deferred split decision
- `B240_adaptive2_r1-360_p80_s20`: Symmetric adaptive split variant
- `B240_adaptive_r1-240_p80_s20`: Same method, narrower r range

## Notes

- Uses sqrt scaling for fair comparison across different r values
- 80 p values provides high resolution for finding optima
- Extended to α=1.5 to explore behavior beyond block capacity
- Large job: 576,000 simulations total
- Fixed boundary condition bug before running (insert_end_pos < left_size)



