# Leaf Splitting Simulation

Comprehensive simulation framework for analyzing B-tree leaf splitting strategies under batch insertions.

## Overview

This project simulates and compares different leaf node splitting methods for B-trees with batch insertions. The framework supports:

- **Three splitting methods**: deferred, immediately, and adaptive
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
    method='adaptive',        # Method: 'deferred', 'immediately', or 'adaptive'
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

### 3. Adaptive Split (NEW!)
- Chooses split point based on insertion location
- Keeps inserted elements in larger block
- **Best for**: p < 0.5 → up to 117% improvement over immediately!

## Performance Summary

| Method      | Best Case          | Fullness | Notes                           |
|-------------|-------------------|----------|----------------------------------|
| Deferred    | α=1.0, p=0.5      | ~0.81    | Highest possible                |
| Immediately | α=0.9, p=0.7      | ~0.69    | Good for high p                 |
| Adaptive    | α=0.75, p=0.2     | ~0.75    | Dramatic improvement at low p   |

## Project Structure

```
.
├── leaf_splitting_sim.py          # Core simulation engine
├── leaf_splitting_sim_slurm.py    # SLURM integration
├── DOCUMENTATION.md                # Complete technical documentation
├── QUICK_REFERENCE.md              # Command reference
├── CSV_COLUMN_REFERENCE.md         # Data format reference
├── analyze/                        # Analysis scripts
│   ├── analyze_results.py
│   └── analyze_results_filtered.py
└── runs/                           # Simulation runs
    ├── B240_adaptive_r1-240_p80_s20/
    ├── B240_immediately_r1-240_p80_s20/
    └── B240_deferred_r1-240_p40_s20/
```

## Key Files

- **`leaf_splitting_sim.py`**: Core simulation with all three methods
- **`leaf_splitting_sim_slurm.py`**: Tools for SLURM cluster execution
- **`DOCUMENTATION.md`**: Detailed technical documentation
- **`QUICK_REFERENCE.md`**: Quick command reference
- **`CSV_COLUMN_REFERENCE.md`**: Output data format

## Documentation

- **[Complete Documentation](DOCUMENTATION.md)**: Methods, algorithms, bug fixes, and implementation details
- **[Quick Reference](QUICK_REFERENCE.md)**: Common commands and workflows
- **[CSV Reference](CSV_COLUMN_REFERENCE.md)**: Output data format

## Recent Updates

### October 17, 2025
- ✅ **Added adaptive splitting method** - up to 117% improvement at p < 0.5
- ✅ **Fixed cascading split bug** in deferred method
- ✅ **Improved error handling** - explicit method validation

## Citation

If you use this code in your research, please cite [your paper/reference here].

## License

[Add your license here]

