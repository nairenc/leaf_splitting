# Immediately Split Simulation Run: B240_immediately_r1-360_p80_s20

**Uses unified framework:** `leaf_splitting_sim_slurm.py` with `method='immediately'`

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
- At α>1.0, immediately method handles overflow by splitting during insertion
- 360 r values provides excellent granularity across the full spectrum

**Experimental Design:**
- Number of seeds: 20
- Method: `immediately` (split during insertion when block fills)
- Batching mode: `batch_by_r` (each task FIXES r, runs all p values)
- Total tasks: **7,200** (20 seeds × 360 r values)
- Total simulations: **576,000** (7,200 tasks × 80 p values)

**Derived Parameters:**
- α (alpha) range: r/B = 1/240 to 360/240 = 0.0042 to 1.5
- Threshold: splits when size reaches B (during insertion)

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
cd /home/nc1827/leaf_splitting/runs/B240_immediately_r1-360_p80_s20
sbatch submit_slurm.sh
```

### Monitor progress:
```bash
# Check job status
squeue -u nc1827

# Watch the latest log
tail -f /scratch/nc1827/leaf_splitting/logs/B240_imm_r360_p80_sweep_*.out

# Count completed results
ls results/result_*.csv | wc -l
```

### After completion:

**Collect results:**
```bash
python ../../leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output B240_immediately_r1-360_p80_s20_results.csv
```

**Analyze results:**
```bash
# Generate overview plots (saves figures in current directory)
python ../../analyze/analyze_results.py \
    --input B240_immediately_r1-360_p80_s20_results.csv

# Generate filtered plots for specific r/B ratios (saves in current directory)
python ../../analyze/analyze_results_filtered.py \
    --input B240_immediately_r1-360_p80_s20_results.csv \
    --r 0.1 0.2 0.4 0.6 0.8 1.0 1.2 1.5
```

## Expected Output

- 7,200 individual CSV files in `results/`
- Combined file: `B240_immediately_r1-360_p80_s20_results.csv` (576,000 records)
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
2. **Overflow handling**: At high α, immediately method handles continuous overflow during insertion
3. **Optimal p at high α**: Previous results showed optimal p≈0.7 at α=1.0; what happens beyond?
4. **Compare methods**: All 4 methods tested with same extended range

### Key Questions:
1. How does optimal p change as α exceeds 1.0?
2. Does fullness continue to increase beyond α=1.0?
3. At what α does immediately method achieve maximum fullness?
4. How does performance compare to deferred/adaptive at α > 1.0?

### Expected Findings:
- Optimal p likely continues to increase with α
- Fullness may plateau or slightly decrease at very high α
- Immediately method may show different patterns than deferred at α > 1.0
- Split behavior becomes more complex at high α

## Comparison Runs

This run complements:
- `B240_deferred_r1-360_p80_s20`: Same parameters, different method
- `B240_adaptive_r1-360_p80_s20`: Same parameters, adaptive split point
- `B240_adaptive2_r1-360_p80_s20`: Same parameters, symmetric adaptive split
- `B240_immediately_r1-240_p80_s20`: Same method, narrower r range

## Notes

- Uses sqrt scaling for fair comparison across different r values
- 80 p values provides high resolution for finding optima
- Extended to α=1.5 to explore behavior beyond block capacity
- Large job: 576,000 simulations total
- Fixed boundary condition bug before running (insert_end_pos < left_size)



