# Adaptive2 Split Simulation Run: B240_adaptive2_r1-240_p80_s20

**Uses unified framework:** `leaf_splitting_sim_slurm.py` with `method='adaptive2'`

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

**Rationale for adaptive2 method:**
- SYMMETRIC version of adaptive method
- Adaptively chooses split point based on insertion location
- **Decision rule:**
  - If `insert_end_pos > (1-p)*B`: split at **(1-p)** position
  - Otherwise: split at **p** position
- Tests the duality hypothesis: Does symmetric adaptive behave differently?
- Completes the 4-way comparison: deferred vs immediately vs adaptive vs adaptive2

**Experimental Design:**
- Number of seeds: 20
- Method: `adaptive2` (symmetric adaptive split point during insertion)
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
cd /home/nc1827/leaf_splitting/runs/B240_adaptive2_r1-240_p80_s20
sbatch submit_slurm.sh
```

### Monitor progress:
```bash
# Check job status
squeue -u nc1827

# Watch the latest log
tail -f /scratch/nc1827/leaf_splitting/logs/B240_adp2_p80_sweep_*.out

# Count completed results
ls results/result_*.csv | wc -l
```

### After completion:

**Collect results:**
```bash
python ../../leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output B240_adaptive2_p80_results.csv
```

**Analyze results:**
```bash
# Generate overview plots (saves figures in current directory)
python ../../analyze/analyze_results.py \
    --input B240_adaptive2_p80_results.csv

# Generate filtered plots for specific r/B ratios (saves in current directory)
python ../../analyze/analyze_results_filtered.py \
    --input B240_adaptive2_p80_results.csv \
    --r 0.1 0.2 0.4 0.6 0.8 1.0
```

## Expected Output

- 4,800 individual CSV files in `results/`
- Combined file: `B240_adaptive2_p80_results.csv` (384,000 records)
- Analysis figures in current directory

## Computational Requirements

- Time per task: ~varies based on r value (larger r = more batches to process)
- Memory per task: 2GB
- Total wall time: depends on cluster load
- Estimated total CPU hours: ~4,800 tasks × avg_time
- Array size: 4,800 tasks

## Scientific Motivation

### What is Adaptive2?

Adaptive2 is the **symmetric counterpart** to the adaptive method:

**Adaptive (original)**:
```
if insert_end_pos < p*B:
  split at p → [p*B, (1-p)*B]
else:
  split at (1-p) → [(1-p)*B, p*B]
```

**Adaptive2 (symmetric)**:
```
if insert_end_pos > (1-p)*B:
  split at (1-p) → [(1-p)*B, p*B]
else:
  split at p → [p*B, (1-p)*B]
```

### Key Observation: Duality

Preliminary tests show a **duality relationship**:
```
Adaptive(p=0.3) ≈ Immediately(p=0.7)
0.5556          ≈ 0.5549 (difference: 0.0006!)
```

This suggests there's a **symmetry in the splitting dynamics** where:
- Different methods achieve similar maximum fullness
- But at different optimal p values
- The choice of split point creates a duality

### Research Questions:

1. **Does adaptive2 create a third distinct performance profile?**
2. **What is the relationship between adaptive2 and the other methods?**
3. **Is there a symmetric duality: Adaptive2(p) ≈ Adaptive(1-p)?**
4. **Which method is truly best for each (α, p) region?**
5. **Do all methods converge to the same maximum fullness limit?**

### Preliminary Results (B=120, r=60):

| p   | Immediately | Adaptive | Adaptive2 | Deferred |
|-----|-------------|----------|-----------|----------|
| 0.2 | 0.3666      | 0.5543   | 0.4016    | 0.4322   |
| 0.3 | 0.4831      | 0.5556   | 0.5230    | 0.5814   |
| 0.5 | 0.5000      | 0.5000   | 0.5000    | 0.5000   |
| 0.7 | 0.5549      | 0.5574   | 0.5030    | 0.5889   |
| 0.8 | 0.5556      | 0.4946   | 0.3712    | 0.4363   |

**Observation**: Adaptive2 has its own distinct behavior!

## Comparison Runs

This completes the 4-way comparison at B=240, full p range:

1. `B240_deferred_r1-240_p40_s20`: p ∈ [0.11, 0.5], 40 values
2. `B240_immediately_r1-240_p80_s20`: p ∈ [0.11, 0.9], 80 values
3. `B240_adaptive_r1-240_p80_s20`: p ∈ [0.11, 0.9], 80 values
4. `B240_adaptive2_r1-240_p80_s20`: **THIS RUN** - p ∈ [0.11, 0.9], 80 values

### Planned 4-Way Analysis:

1. **Maximum fullness vs α**: Which method achieves highest fullness at each α?
2. **Optimal p vs α**: How does optimal p change with α for each method?
3. **Duality verification**: Test Adaptive(p) ≈ Immediately(1-p) across all α
4. **Symmetry test**: Test Adaptive2(p) vs Adaptive(p) vs Adaptive(1-p)
5. **Performance regions**: Map the (α, p) space to optimal method

## Expected Findings

Based on preliminary tests and duality observations:

1. **All methods likely achieve similar maximum fullness**
   - But at different optimal p values
   - Fundamental limit determined by α, not method

2. **Duality relationships expected**:
   - Adaptive(p) ≈ Immediately(1-p)
   - Possibly: Adaptive2(p) ≈ something else?

3. **Deferred still best at α=1.0, p=0.5**
   - Achieves ~0.81 fullness (unique to deferred)

4. **Different methods = different p preferences**
   - Not better performance, just different operating points

## Notes

- Uses sqrt scaling for fair comparison across different r values
- 80 p values provides high resolution for finding crossover points
- Large job: 384,000 simulations total
- Completes comprehensive 4-method comparison
- Will reveal fundamental structure of the splitting problem

## Implementation Note

Make sure the updated `leaf_splitting_sim.py` with the `adaptive2` method is deployed before running this job!

