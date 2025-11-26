# Leaf Splitting Simulation

Comprehensive simulation framework for analyzing B-tree leaf splitting strategies under batch insertions.

## Overview

This project simulates and compares different leaf node splitting methods for B-trees with batch insertions. The framework supports:

- **Five splitting methods**: deferred, immediately, adaptive, adaptive2, and phased
- **Histogram-based simulation**: Efficient simulation of millions of insertions
- **SLURM integration**: Parallel execution on HPC clusters
- **Comprehensive analysis**: Automated result collection and visualization

## Quick Start

### Running a Single Simulation

```python
from leaf_splitting_sim import simulate

result = simulate(
    B=120,                    # Block capacity
    r=60,                     # Batch size
    total_insertions=100000,  # Total keys to insert
    method='adaptive',        # Method: 'deferred', 'immediately', 'adaptive', 'adaptive2', or 'phased'
    p=0.3,                    # Split ratio
    seed=42                   # Random seed
)

print(f"Final fullness: {result['final_fullness']:.4f}")
```

### Generating a Sweep Configuration

```bash
python leaf_splitting_sim_slurm.py config \
    --B 240 \
    --method adaptive \
    --r_min 1 --r_max 240 \
    --p_min 0.11 --p_max 0.9 --p_count 80 \
    --seeds 20 \
    --batch_by_r \
    --output sweep_config.json
```

### Running on SLURM

```bash
cd runs/B240_adaptive_r1-240_p80_s20
sbatch submit_slurm.sh
```

## Methods

### 1. Deferred Split
- Inserts entire batch first, then splits if needed
- Can temporarily exceed capacity
- **Best for**: α = 1.0 (r = B) with p ≈ 0.5 → achieves ~0.81 fullness!

### 2. Immediately Split  
- Splits incrementally during insertion
- Never exceeds capacity
- **Best for**: p > 0.6 at high α

### 3. Adaptive Split
- Chooses split point based on insertion location
- Keeps inserted elements in larger block
- **Best for**: p < 0.5 → up to 117% improvement over immediately!

### 4. Adaptive2 Split
- Symmetric adaptive strategy
- Split at 1-p if insertion at end, else p
- Alternative adaptive approach

### 5. Phased Split
- Uses p=0.5 for first N/16 elements, then p=0.49
- Combines even split with slight adjustment
- Time-dependent strategy

## Performance Summary

| Method      | Best Case          | Fullness | Notes                           |
|-------------|-------------------|----------|----------------------------------|
| Deferred    | α=1.0, p=0.5      | ~0.81    | Highest possible                |
| Immediately | α=0.9, p=0.7      | ~0.69    | Good for high p                 |
| Adaptive    | α=0.75, p=0.2     | ~0.75    | Dramatic improvement at low p   |
| Adaptive2   | -                 | -        | Symmetric variant of adaptive   |
| Phased      | -                 | -        | Time-dependent strategy         |

## Project Structure

```
.
├── core/                              # Core simulation and analysis scripts
│   ├── leaf_splitting_sim.py          # Main simulation engine
│   ├── leaf_splitting_sim_slurm.py    # SLURM parameter sweeps
│   ├── leaf_splitting_sim_even_split_slurm.py  # Even split SLURM (multiple B)
│   ├── leaf_splitting_sim_sequence.py # Variable batch size simulations
│   ├── leaf_splitting_sim_sequence_slurm.py  # SLURM for sequences
│   ├── compare_split_strategies_r1.py # Compare strategies for r=1
│   ├── compare_split_strategies_r1_slurm.py  # SLURM version
│   ├── check_even_split_optimal.py    # Theoretical analysis (probability)
│   ├── check_even_split_optimal_matrix.py  # Theoretical analysis (matrix)
│   ├── find_optimal_split_eigenvector.py  # Eigenvector analysis
│   └── simulate_variable_r.py          # Legacy variable r (deprecated)
│   └── README.md                      # Core module documentation
├── analyze/                           # Analysis and plotting scripts
│   ├── analyze_results.py            # Result analysis and visualization
│   ├── analyze_results_filtered.py   # Filtered analysis
│   └── plot_convergence.py           # Convergence visualization
├── runs/                              # Simulation run directories
│   ├── Fix_R/                        # Fixed r parameter sweeps
│   └── Var_R/                        # Variable r sequence runs
├── README.md                          # This file - project overview
├── USER_GUIDE.md                      # Complete user guide
├── TECHNICAL_DOCS.md                  # Algorithms & implementation
├── SEQUENCE_GUIDE.md                  # Sequence simulations guide
└── QUICK_ANALYSIS.md                  # Quick analysis guide
```

**See [core/README.md](core/README.md) for detailed documentation of all core scripts.**

## 📚 Documentation

### Main Guides (Start Here!)

1. **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user guide
   - Quick commands & workflow
   - SLURM execution guide
   - Analysis tools & plotting
   - Understanding metrics (time-avg vs final fullness)
   - CSV data format

2. **[SEQUENCE_GUIDE.md](SEQUENCE_GUIDE.md)** - Variable batch sizes (r_sequence)
   - How to use r_sequence for time-varying workloads
   - SLURM execution with convergence tracking
   - Output format (long-format CSV with snapshots)
   - Python API & examples

3. **[TECHNICAL_DOCS.md](TECHNICAL_DOCS.md)** - For developers
   - Algorithms & implementation details
   - Bug fixes & updates
   - Performance analysis

### 🛠️ Key Scripts

- **`core/leaf_splitting_sim.py`**: Core simulation (fixed r sweeps)
- **`core/leaf_splitting_sim_slurm.py`**: SLURM parameter sweeps
- **`core/leaf_splitting_sim_even_split_slurm.py`**: SLURM for even split (p=0.5) with multiple B values
- **`core/leaf_splitting_sim_sequence.py`**: Variable batch sizes with convergence tracking
- **`core/leaf_splitting_sim_sequence_slurm.py`**: SLURM for sequences
- **`analyze/plot_convergence.py`**: Visualize convergence over time
- **`analyze/analyze_results.py`**: Analysis & plotting for parameter sweeps

## Even Split Simulations

For comprehensive even split (p=0.5) studies with multiple B values:

```bash
# Generate config - r values auto-generated from 1 to B/2+1
python core/leaf_splitting_sim_even_split_slurm.py config \
    --B-min 256 --B-max 512 --B-step 1 \
    --method deferred \
    --seeds 20 \
    --output even_split_config.json

# Submit to SLURM
cd runs/your_run_directory
sbatch submit_slurm.sh

# Collect results
python core/leaf_splitting_sim_even_split_slurm.py collect \
    --results_dir results \
    --output aggregated_results.csv
```

**Key features:**
- Auto-generates r values from 1 to B/2+1 for each B
- Each task = (B, seed) combination, runs all r values
- No need to specify r range manually
- Perfect for studying even split behavior across many B values

See [USER_GUIDE.md](USER_GUIDE.md) for detailed workflow.

## Recent Updates

### November 26, 2025
- ✅ **Even split SLURM script** - New `leaf_splitting_sim_even_split_slurm.py` for comprehensive B/r sweeps
- ✅ **Auto-generated r values** - Automatically generates r from 1 to B/2+1 per B value

### November 10, 2025
- ✅ **Convergence tracking** - Record fullness at multiple time points (100 snapshots)
- ✅ **Long-format CSV output** - Clean relational format (one row per snapshot)
- ✅ **Convergence visualization** - `plot_convergence.py` to see when steady state is reached
- ✅ **Cleaned documentation** - Consolidated from 6+ files to 3 focused guides

### October 17, 2025
- ✅ **Added adaptive splitting method** - up to 117% improvement at p < 0.5
- ✅ **Fixed cascading split bug** in deferred method
- ✅ **Improved error handling** - explicit method validation

## Getting Started

1. **New users**: Start with [USER_GUIDE.md](USER_GUIDE.md)
2. **Running sequences**: See [SEQUENCE_GUIDE.md](SEQUENCE_GUIDE.md)
3. **Analyzing results**: See [QUICK_ANALYSIS.md](QUICK_ANALYSIS.md)
4. **Understanding algorithms**: Read [TECHNICAL_DOCS.md](TECHNICAL_DOCS.md)

## Citation

If you use this code in your research, please cite [your paper/reference here].

## License

[Add your license here]

