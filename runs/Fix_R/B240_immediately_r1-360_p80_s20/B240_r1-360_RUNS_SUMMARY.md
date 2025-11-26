# B240 Extended Runs Summary: r=1-360, α up to 1.5

## Overview

This document summarizes the 4 new simulation runs with extended r values (1-360), exploring behavior beyond α=1.0 (when batch size exceeds block capacity).

## Run Directories

1. **`B240_deferred_r1-360_p80_s20/`** - Deferred split method
2. **`B240_immediately_r1-360_p80_s20/`** - Immediately split method  
3. **`B240_adaptive_r1-360_p80_s20/`** - Adaptive split method
4. **`B240_adaptive2_r1-360_p80_s20/`** - Symmetric adaptive split method

## Configuration Details

**Shared Parameters:**
- Block size (B): **240**
- Batch size range (r): **1 to 360** (360 values) ← Extended from 1-240
- Split ratio range (p): **0.11 to 0.9** (80 values)
- Number of seeds: **20**
- Insertion scaling: **sqrt** (`total_insertions = (sqrt(r) + 1) × 100,000`)
- Batching mode: **batch_by_r** (each task fixes r, runs all p values)

**Scale:**
- Total tasks per run: **7,200** (20 seeds × 360 r values)
- Total simulations per run: **576,000** (7,200 tasks × 80 p values)
- **Grand total**: **2,304,000 simulations** across all 4 methods

**α (alpha) range:**
- Minimum: 1/240 = **0.0042**
- Maximum: 360/240 = **1.5** ← Extends beyond block capacity!

## Why Extend to r=360 (α=1.5)?

### Scientific Motivation

1. **Beyond capacity regime**: Explore behavior when batch size exceeds block capacity
2. **Cascading splits**: At α > 1.0, understand how different methods handle overflow
3. **Optimal p at high α**: Previous results showed optimal p≈0.7 at α=1.0; what happens beyond?
4. **Method comparison**: Compare all 4 methods across same extended range
5. **Complete picture**: Understand fullness behavior across full α spectrum

### Key Questions

1. How does fullness change as α exceeds 1.0?
2. Do different methods behave differently at α > 1.0?
3. What is the optimal p for each method at high α?
4. At what α does each method achieve maximum fullness?
5. Does adaptive/adaptive2 provide benefits at high α?

## Method Descriptions

### 1. Deferred (`deferred`)
- Insert entire batch, then split if size ≥ B
- At α > 1.0: Creates cascading splits
- Expected behavior: Multiple splits per insertion at high α

### 2. Immediately (`immediately`)
- Split during insertion when block reaches capacity
- Fixed split point at position p
- Expected behavior: Continuous overflow handling at high α

### 3. Adaptive (`adaptive`)
- Dynamic split point based on insertion location
- If insertion < p×B: split at p
- If insertion ≥ p×B: split at (1-p)
- Expected behavior: Adapts to keep inserted elements in larger block

### 4. Adaptive2 (`adaptive2`)
- Symmetric version of adaptive
- If insertion > (1-p)×B: split at (1-p)
- Otherwise: split at p
- Expected behavior: Symmetric treatment of insertions at opposite ends

## File Structure

Each run directory contains:
```
B240_{method}_r1-360_p80_s20/
├── sweep_config.json       # Configuration with r=1-360
├── submit_slurm.sh         # SLURM script (array 0-7199)
├── README.md               # Detailed documentation
└── results/                # Output directory for CSV files
```

## Submitting Jobs

Submit all 4 runs:
```bash
cd /home/nc1827/leaf_splitting/runs

# Submit deferred
cd B240_deferred_r1-360_p80_s20
sbatch submit_slurm.sh
cd ..

# Submit immediately
cd B240_immediately_r1-360_p80_s20
sbatch submit_slurm.sh
cd ..

# Submit adaptive
cd B240_adaptive_r1-360_p80_s20
sbatch submit_slurm.sh
cd ..

# Submit adaptive2
cd B240_adaptive2_r1-360_p80_s20
sbatch submit_slurm.sh
cd ..
```

Or submit all at once:
```bash
cd /home/nc1827/leaf_splitting/runs
for method in deferred immediately adaptive adaptive2; do
    cd B240_${method}_r1-360_p80_s20
    sbatch submit_slurm.sh
    cd ..
done
```

## Monitoring Progress

```bash
# Check all jobs
squeue -u nc1827

# Count completed results for each method
for method in deferred immediately adaptive adaptive2; do
    echo "$method: $(ls B240_${method}_r1-360_p80_s20/results/result_*.csv 2>/dev/null | wc -l) / 7200"
done

# Watch logs
tail -f /scratch/nc1827/leaf_splitting/logs/B240_*_r360_p80_sweep_*.out
```

## After Completion

### Collect results for each method:
```bash
cd /home/nc1827/leaf_splitting/runs

for method in deferred immediately adaptive adaptive2; do
    cd B240_${method}_r1-360_p80_s20
    python ../../leaf_splitting_sim_slurm.py collect \
        --results_dir results \
        --output B240_${method}_r1-360_p80_s20_results.csv
    cd ..
done
```

### Analyze results:
```bash
# For each method
for method in deferred immediately adaptive adaptive2; do
    cd B240_${method}_r1-360_p80_s20
    
    # Generate overview plots
    python ../../analyze/analyze_results.py \
        --input B240_${method}_r1-360_p80_s20_results.csv
    
    # Generate filtered plots including α > 1.0
    python ../../analyze/analyze_results_filtered.py \
        --input B240_${method}_r1-360_p80_s20_results.csv \
        --r 0.1 0.2 0.4 0.6 0.8 1.0 1.2 1.5
    
    cd ..
done
```

## Computational Requirements

**Per run:**
- Array size: 7,200 tasks
- Time limit: 12 hours per task
- Memory: 2GB per task
- Estimated wall time: Depends on cluster load

**Total across all 4 runs:**
- Total tasks: 28,800
- Total simulations: 2,304,000
- This is a large-scale experiment!

## Important Notes

### Code Improvements Before Running

1. **Boundary bug fixed**: Changed `insert_end_pos <= left_size` to `insert_end_pos < left_size` in all methods
2. **Code refactored**: Merged duplicate cases for cleaner, more maintainable code
3. **All methods updated**: immediately, adaptive, and adaptive2 all have the fixes

### Scientific Value

This extended range will:
- Complete our understanding of α spectrum
- Reveal how methods behave beyond block capacity
- Help identify optimal strategies for different α regimes
- Enable comprehensive method comparison

## Expected Timeline

Assuming similar performance to previous runs:
- Submit: Day 0
- First results: Day 0-1
- Completion: Day 1-3 (depending on cluster load)
- Collection & analysis: Day 3-4

## Comparison with Previous Runs

| Run Name | r range | α range | Tasks | Sims | Status |
|----------|---------|---------|-------|------|--------|
| B240_deferred_r1-240_p40_s20 | 1-240 | 0.004-1.0 | 4,800 | 192,000 | Complete |
| B240_immediately_r1-240_p80_s20 | 1-240 | 0.004-1.0 | 4,800 | 384,000 | Complete |
| B240_adaptive_r1-240_p80_s20 | 1-240 | 0.004-1.0 | 4,800 | 384,000 | Complete |
| B240_adaptive2_r1-240_p80_s20 | 1-240 | 0.004-1.0 | 4,800 | 384,000 | Complete |
| **B240_deferred_r1-360_p80_s20** | **1-360** | **0.004-1.5** | **7,200** | **576,000** | **NEW** |
| **B240_immediately_r1-360_p80_s20** | **1-360** | **0.004-1.5** | **7,200** | **576,000** | **NEW** |
| **B240_adaptive_r1-360_p80_s20** | **1-360** | **0.004-1.5** | **7,200** | **576,000** | **NEW** |
| **B240_adaptive2_r1-360_p80_s20** | **1-360** | **0.004-1.5** | **7,200** | **576,000** | **NEW** |

## Contact

Created: November 5, 2025
By: Automated run setup
For questions: See individual README.md files in each run directory

