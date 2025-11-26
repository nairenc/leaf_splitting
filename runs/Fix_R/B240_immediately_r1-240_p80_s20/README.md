# Immediately Split Simulation Run: B240_immediately_r1-240_p80_s20

**Uses unified framework:** `leaf_splitting_sim_slurm.py` with `method='immediately'`

## Configuration

**Block and Batch Parameters:**
- Block size (B): 240
- Batch size range (r): 1 to 240 (240 values, step=1)
- Split ratio range (p): **0.11 to 0.9 (80 values)** ← Extended range!
- **Insertion strategy**: sqrt scaling
  - Formula: `total_insertions = (sqrt(r) + 1) × 100,000`
  - r=1: 200,000 insertions
  - r=16: 500,000 insertions
  - r=64: 900,000 insertions
  - r=120: 1,195,445 insertions
  - r=240: 1,649,193 insertions

**Rationale for B=240 and extended p range:**
- Larger B provides finer granularity for α = r/B ratios
- α range: 1/240 to 240/240 = 0.0042 to 1.0 (twice the resolution of B=120)
- Extended p range (0.11-0.9) captures full behavior including optimal p at high α
- 80 p values gives fine granularity (step size ≈0.01)

**Experimental Design:**
- Number of seeds: 20
- Method: `immediately` (split during insertion)
- Batching mode: `batch_by_r` (each task FIXES r, runs all p values)
- Total tasks: 4,800 (20 seeds × 240 r values)
- Total simulations: **384,000** (4,800 tasks × 80 p values)

**Derived Parameters:**
- α (alpha) range: r/B = 1/240 to 240/240 = 0.0042 to 1.0
- Threshold: splits when size reaches B (during insertion)

## Task Distribution

Each SLURM array task handles:
- One (seed, r) combination
- Runs all 80 p values for that combination
- Total: 80 simulations per task

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
cd /home/nc1827/leaf_splitting/runs/B240_immediately_r1-240_p80_s20
sbatch submit_slurm.sh
```

### Monitor progress:
```bash
# Check job status
squeue -u nc1827

# Watch the latest log
tail -f /scratch/nc1827/leaf_splitting/logs/B240_imm_p80_sweep_*.out

# Count completed results
ls results/result_*.csv | wc -l
```

### After completion:

**Collect results:**
```bash
python ../../leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output B240_immediately_p80_results.csv
```

**Analyze results:**
```bash
# Generate overview plots (saves figures in current directory)
python ../../analyze/analyze_results.py \
    --input B240_immediately_p80_results.csv

# Generate filtered plots for specific r/B ratios (saves in current directory)
python ../../analyze/analyze_results_filtered.py \
    --input B240_immediately_p80_results.csv \
    --r 0.1 0.2 0.4 0.6 0.8 1.0
```

## Expected Output

- 4,800 individual CSV files in `results/`
- Combined file: `B240_immediately_p80_results.csv` (384,000 records)
- Analysis figures in current directory

## Computational Requirements

- Time per task: ~varies based on r value (larger r = more batches to process)
- Memory per task: 2GB
- Total wall time: depends on cluster load
- Estimated total CPU hours: ~4,800 tasks × avg_time
- Array size: 4,800 tasks

## Scientific Motivation

### Why B=240?

1. **Finer α granularity**: α = r/B has step size of 1/240 ≈ 0.0042 (vs 1/120 ≈ 0.0083 for B=120)
2. **Larger scale**: Tests scalability of immediately method to larger block sizes
3. **Better resolution**: More data points across the α spectrum
4. **Comparison with deferred**: B240_deferred run can be compared directly

### Why extend p range to 0.9?

Previous analysis showed:
- When r=B (α=1.0), immediately method achieves maximum fullness at p≈0.7
- Need to explore p ∈ [0.5, 0.9] to capture:
  - Optimal p for different r values
  - Behavior at extreme p values
  - Complete picture of immediately method performance

### Key Questions:
1. How does optimal p change with α = r/B?
2. Does B=240 change the optimal p compared to B=120?
3. At what α does immediately method perform best?
4. Can immediately beat deferred at high α with optimal p?
5. What happens at very high p (0.8-0.9)?

### Expected Findings:
- For high α (r close to B): optimal p likely in [0.6, 0.8]
- For low α (small r): optimal p likely near 0.5
- Scaling behavior should be similar to B=120 but with finer detail
- Maximum fullness at α=1.0 should be similar (~0.57 at p≈0.7)

## Comparison Runs

This run complements:
- `B120_immediately_r1-120_p80_s20`: Same p range, smaller B
- `B240_deferred_r1-240_p40_s20`: Same B, different method, narrower p range
- Future: Consider `B240_deferred_r1-240_p80_s20` for complete comparison

## Notes

- Uses sqrt scaling for fair comparison across different r values
- 80 p values provides high resolution for finding optima
- Large job: 384,000 simulations total
- May want to run deferred with extended p range too for complete picture


