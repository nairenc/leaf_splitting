# Adaptive Split Simulation Run: B240_adaptive_r1-240_p80_s20

**Uses unified framework:** `leaf_splitting_sim_slurm.py` with `method='adaptive'`

## Configuration

**Block and Batch Parameters:**
- Block size (B): 240
- Batch size range (r): 1 to 240 (240 values, step=1)
- Split ratio range (p): **0.11 to 0.9 (80 values)** ← Full range!
- **Insertion strategy**: sqrt scaling
  - Formula: `total_insertions = (sqrt(r) + 1) × 100,000`
  - r=1: 200,000 insertions
  - r=16: 500,000 insertions
  - r=64: 900,000 insertions
  - r=120: 1,195,445 insertions
  - r=240: 1,649,193 insertions

**Rationale for adaptive method:**
- NEW method that adaptively chooses split point based on insertion location
- When insertion ends before p*B: split at p (as usual)
- When insertion ends at/after p*B: split at (1-p) instead
- **Key advantage**: Keeps newly inserted elements in larger block → better packing
- Expected to **dramatically outperform immediately** when p < 0.5 (up to 117% improvement!)
- Expected to **match immediately** when p = 0.5
- May underperform when p > 0.5, but still worth testing

**Experimental Design:**
- Number of seeds: 20
- Method: `adaptive` (adaptive split point during insertion)
- Batching mode: `batch_by_r` (each task FIXES r, runs all p values)
- Total tasks: 4,800 (20 seeds × 240 r values)
- Total simulations: **384,000** (4,800 tasks × 80 p values)

**Derived Parameters:**
- α (alpha) range: r/B = 1/240 to 240/240 = 0.0042 to 1.0
- Threshold: splits when size reaches B (during insertion with adaptive point)

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
cd /home/nc1827/leaf_splitting/runs/B240_adaptive_r1-240_p80_s20
sbatch submit_slurm.sh
```

### Monitor progress:
```bash
# Check job status
squeue -u nc1827

# Watch the latest log
tail -f /scratch/nc1827/leaf_splitting/logs/B240_adp_p80_sweep_*.out

# Count completed results
ls results/result_*.csv | wc -l
```

### After completion:

**Collect results:**
```bash
python ../../leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output B240_adaptive_p80_results.csv
```

**Analyze results:**
```bash
# Generate overview plots (saves figures in current directory)
python ../../analyze/analyze_results.py \
    --input B240_adaptive_p80_results.csv

# Generate filtered plots for specific r/B ratios (saves in current directory)
python ../../analyze/analyze_results_filtered.py \
    --input B240_adaptive_p80_results.csv \
    --r 0.1 0.2 0.4 0.6 0.8 1.0
```

## Expected Output

- 4,800 individual CSV files in `results/`
- Combined file: `B240_adaptive_p80_results.csv` (384,000 records)
- Analysis figures in current directory

## Computational Requirements

- Time per task: ~varies based on r value (larger r = more batches to process)
- Memory per task: 2GB
- Total wall time: depends on cluster load
- Estimated total CPU hours: ~4,800 tasks × avg_time
- Array size: 4,800 tasks

## Scientific Motivation

### What is the Adaptive Method?

The adaptive method is an **enhancement** of the immediately method:
- **Immediately**: Always splits at position p*B
- **Adaptive**: Chooses split point (p or 1-p) based on insertion location

**Algorithm:**
```
When block reaches capacity B during insertion at position t:
  insert_end_pos = position where insertion ends
  if insert_end_pos < p*B:
    split at p → blocks [p*B, (1-p)*B]
  else:
    split at (1-p) → blocks [(1-p)*B, p*B]
```

### Expected Performance (from tests):

**When p < 0.5** (HUGE improvements expected):
- α=0.75, p=0.2: +117% improvement vs immediately
- α=0.90, p=0.2: +114% improvement vs immediately
- α=1.00, p=0.2: +83% improvement vs immediately
- α=0.50, p=0.3: +17% improvement vs immediately

**When p = 0.5** (identical):
- Same as immediately method (symmetric splits)

**When p > 0.5** (some degradation expected):
- α=0.90, p=0.8: -31% vs immediately
- α=0.75, p=0.7: -26% vs immediately
- Still worth testing to understand full behavior

### Key Research Questions:

1. **Does adaptive beat immediately across the board for p < 0.5?**
2. **At what p value does adaptive transition from better to worse?**
3. **How does α affect the crossover point?**
4. **Can adaptive beat deferred at any (α, p) combination?**
5. **What is the optimal method for each region of (α, p) space?**

### Why Test Full p Range (0.11-0.9)?

Even though adaptive may underperform at p > 0.5, we need the full data to:
- Understand the complete performance landscape
- Find the exact crossover point
- Enable fair 3-way comparison: deferred vs immediately vs adaptive
- Identify optimal method for each (α, p) region

## Comparison Runs

This run enables comprehensive comparison:
- `B240_deferred_r1-240_p40_s20`: Same B, p ∈ [0.11, 0.5]
- `B240_immediately_r1-240_p80_s20`: Same B, same p range, different method
- `B240_adaptive_r1-240_p80_s20`: **THIS RUN** - Same as immediately but adaptive

### Planned Analysis:

Direct comparison plots:
1. **Fullness vs p** for each α: Show all 3 methods
2. **Fullness vs α** for each p: Identify best method per region
3. **Heatmaps**: (α, p) → fullness for each method
4. **Difference plots**: adaptive - immediately, adaptive - deferred

## Notes

- Uses sqrt scaling for fair comparison across different r values
- 80 p values provides high resolution for finding crossover points
- Large job: 384,000 simulations total
- First comprehensive test of the new adaptive method at scale
- Results will guide future method selection for different workloads

## Expected Findings

Based on preliminary tests, we expect:
- **Adaptive dominates for p < 0.5** (especially p = 0.2-0.4)
- **Three-way tie at p = 0.5**
- **Immediately wins for p > 0.6**
- **Deferred still best at α = 1.0, p = 0.5** (~0.81 fullness)

The full results will reveal the complete performance landscape!

