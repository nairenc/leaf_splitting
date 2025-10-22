# Quick Reference - Unified Leaf Splitting Framework

## Common Commands

### Generate Configuration

```bash
python leaf_splitting_sim_slurm.py config \
    --B 120 \
    --method deferred \              # or 'immediately'
    --r_min 1 --r_max 120 --r_step 1 \
    --p_min 0.11 --p_max 0.5 --p_count 40 \
    --seeds 20 \
    --insertion_scale sqrt \         # or 'linear' or 'fixed'
    --base_insertions 100000 \
    --batch_by_r \                   # Fix r, vary p
    --output sweep_config.json
```

### Submit to SLURM

```bash
cd runs/your_run_name
sbatch submit_slurm.sh
```

### Collect Results

```bash
python leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output final_results.csv
```

### Analyze Results

```bash
# Overview plots
python analyze/analyze_results.py --input final_results.csv

# Filtered plots (specific r or p values)
python analyze/analyze_results_filtered.py \
    --input final_results.csv \
    --R 1 60 120              # Specific r values
    
python analyze/analyze_results_filtered.py \
    --input final_results.csv \
    --r 0.25 0.5 0.75         # Specific α = r/B ratios
```

## Methods

| Method | Description | Sampling | Split Trigger |
|--------|-------------|----------|---------------|
| `deferred` | Split decision after insertion | ∝ (size + 1) | size ≥ B |
| `immediately` | Split during insertion | ∝ size (with position) | size ≥ B |

## Batching Modes

| Mode | Meaning | Tasks | Each Task Runs |
|------|---------|-------|----------------|
| `batch_by_r` | **Fix r**, vary p | seeds × r_values | All p values |
| `batch_by_p` | **Fix p**, vary r | seeds × p_values | All r values |
| Neither | Individual | seeds × r × p | Single combination |

## Insertion Scaling

| Strategy | Formula | Use Case |
|----------|---------|----------|
| `sqrt` | `(√r + 1) × base` | Balanced load (recommended) |
| `linear` | `r × base` | Linear scaling |
| `fixed` | `total_insertions` | Same for all r |

## File Structure

```
leaf_splitting/
├── leaf_splitting_sim.py              # Core simulation library
├── leaf_splitting_sim_slurm.py        # SLURM runner
├── UNIFIED_FRAMEWORK.md               # Detailed documentation
├── QUICK_REFERENCE.md                 # This file
├── analyze/
│   ├── analyze_results.py             # Overview plots
│   └── analyze_results_filtered.py    # Filtered plots
└── runs/
    └── your_run_name/
        ├── sweep_config.json          # Generated config
        ├── submit_slurm.sh            # SLURM submission script
        ├── results/                   # Individual task CSVs
        └── README.md                  # Run documentation
```

## Typical Workflow

1. **Create config:**
   ```bash
   python leaf_splitting_sim_slurm.py config --B 120 --method deferred \
       --r_min 1 --r_max 120 --p_count 40 --seeds 20 \
       --insertion_scale sqrt --batch_by_r --output runs/myrun/sweep_config.json
   ```

2. **Create submit script:**
   ```bash
   cp submit_slurm_template.sh runs/myrun/submit_slurm.sh
   # Edit to set correct paths and array size
   ```

3. **Submit:**
   ```bash
   cd runs/myrun
   sbatch submit_slurm.sh
   ```

4. **Monitor:**
   ```bash
   squeue -u $USER
   tail -f /scratch/$USER/leaf_splitting/logs/*.out
   ```

5. **Collect:**
   ```bash
   python ../../leaf_splitting_sim_slurm.py collect \
       --results_dir results --output results.csv
   ```

6. **Analyze:**
   ```bash
   python ../../analyze/analyze_results.py --input results.csv
   ```

## CSV Columns

Output from both methods:
```
task_id          - SLURM task ID
B                - Block capacity
r                - Batch size
alpha            - r/B ratio
p                - Split ratio
seed             - Random seed
fullness         - Final fullness
time_avg_fullness - Time-averaged fullness
```

## Quick Tests

```bash
# Test deferred (small)
python leaf_splitting_sim.py  # Runs built-in test

# Test immediately (small)
from leaf_splitting_sim import simulate
result = simulate(B=120, r=60, total_insertions=10000, 
                 method='immediately', p=0.3, seed=42)
print(result['final_fullness'])
```

## Common Issues

**Problem:** `KeyError: 'method'`  
**Solution:** Add `"method": "deferred"` or `"method": "immediately"` to sweep_config.json

**Problem:** Results files not found  
**Solution:** Check `--results_dir` path and look for `result_*.csv` (not `task_*.csv`)

**Problem:** Simulation seems slow  
**Solution:** With histogram optimization, 100k insertions should take <1s. Check parameters.

## Performance

Histogram optimization makes both methods blazing fast:
- ✅ 100k insertions: ~0.01-0.05s
- ✅ Can run millions of insertions quickly
- ✅ No need for warm_start (removed)

## Getting Help

See detailed documentation:
- `UNIFIED_FRAMEWORK.md` - Complete framework guide
- `SLURM_USAGE.md` - SLURM-specific help
- `SETUP_NEW_RUN.md` - How to create new runs

