# Test Run: Deferred Split B120

## Purpose
Test run to verify the deferred split simulation works correctly on SLURM with full p-value sweep before running the complete r-value sweep.

**Uses unified framework:** `leaf_splitting_sim_slurm.py` with `method='deferred'`

**Direct comparison with** `test_immediately_B120` - same parameters, different split method.

## Configuration

**Test Parameters:**
- Block size (B): 120
- Batch sizes (r): **2 values only** - [1, 60]
- Split ratio (p): **40 values** - 0.11 to 0.5 (full p sweep)
- Seeds: **20 seeds** (full seed set)

**Insertion Strategy:**
- sqrt scaling: `(sqrt(r) + 1) × 100,000`
- r=1: 200,000 insertions
- r=60: 874,596 insertions

**Task Structure:**
- Method: `deferred` (deferred split)
- Batch mode: `batch_by_r` (each task FIXES r, runs all p values)
- Total tasks: **40** (20 seeds × 2 r values)
- Simulations per task: 40 (all p values)
- Total simulations: 1,600

## Task Breakdown

- Task 0-1: seed 0, r=[1, 60], each runs 40 p values
- Task 2-3: seed 1, r=[1, 60], each runs 40 p values
- ...
- Task 38-39: seed 19, r=[1, 60], each runs 40 p values

## Running

```bash
cd /home/nc1827/leaf_splitting/runs/test_deferred_B120
sbatch submit_slurm.sh
```

## Expected Runtime

- Total tasks: 40
- Time per task: ~5-30 minutes (depends on r value, each runs 40 p values)
- Total wall time: ~30-60 minutes (parallel execution)

## After Completion

**Collect results:**
```bash
python ../../leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output test_results.csv
```

**Check results:**
```bash
# Should show 40 result files
ls results/result_*.csv | wc -l

# View combined results
head -20 test_results.csv
```

Should have 1,600 records (20 seeds × 2 r values × 40 p values).

**Analyze (optional):**
```bash
# Quick plot to verify results look reasonable
python ../../analyze/analyze_results_filtered.py \
    --input test_results.csv \
    --R 1 60
```

## Verification

After collecting, you should see:
- 40 result files in `results/` (one per seed×r combination)
- `test_results.csv` with 1,600 data rows
- Logs in `/scratch/nc1827/leaf_splitting/logs/test_def_B120_*.out`
- Each task should complete successfully

## CSV Output

**Columns** (minimal format):
```csv
task_id,B,r,alpha,p,seed,fullness,time_avg_fullness
```

Only 8 columns - streamlined for efficiency!

## Comparison Tests

Once both test runs complete, you can directly compare:

```bash
# Compare deferred vs immediately split for r=1
python ../../analyze/analyze_results_filtered.py \
    --input test_results.csv --R 1

# View both on same plot (if you combine CSVs)
```

If both tests pass, you can confidently submit the full runs:
- `B120_r1-120_p40_s20_n100k` (deferred, 2,400 tasks with all 120 r values)
- `immediately_B120_r1-120_p40_s20` (immediate, 2,400 tasks with all 120 r values)

