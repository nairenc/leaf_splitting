# Core Module Documentation

This directory contains the core simulation and analysis scripts for leaf splitting simulations.

## Main Simulation Scripts

### `leaf_splitting_sim.py`
**Core simulation engine** - The main simulation module used by all other scripts.

**Key functions:**
- `simulate()` - Run a single simulation with fixed batch size r
- `simulate_variable_r()` - Run simulation with variable batch sizes (r_sequence)
- `compute_split_size()` - Calculate split sizes based on ratio p
- `insert_deferred_split()` - Deferred splitting logic
- `insert_with_position_split()` - Immediate/adaptive splitting logic

**Usage:**
```python
from core.leaf_splitting_sim import simulate

result = simulate(
    B=120, r=60, total_insertions=100000,
    method='deferred', p=0.5, seed=42
)
```

**Supported methods:**
- `'deferred'` - Insert batch first, then split
- `'immediately'` - Split during insertion
- `'adaptive'` - Adaptive split based on insertion location
- `'adaptive2'` - Symmetric adaptive
- `'phased'` - Phased strategy with different p at different stages

---

## SLURM Scripts

### `leaf_splitting_sim_slurm.py`
**SLURM parameter sweeps** - For running large parameter sweeps on HPC clusters.

**Commands:**
- `config` - Generate configuration file
- `run` - Run a single task (called by SLURM)
- `collect` - Collect and aggregate results

**Usage:**
```bash
# Generate config
python core/leaf_splitting_sim_slurm.py config \
    --B 240 --method deferred \
    --r-min 1 --r-max 240 \
    --p-min 0.11 --p-max 0.9 --p-count 80 \
    --seeds 20 --output sweep_config.json

# Run task (typically via SLURM)
python core/leaf_splitting_sim_slurm.py run \
    --config sweep_config.json \
    --task_id 0 \
    --output_dir results

# Collect results
python core/leaf_splitting_sim_slurm.py collect \
    --results_dir results \
    --output aggregated_results.csv
```

**See:** [USER_GUIDE.md](../USER_GUIDE.md) for detailed workflow

---

### `leaf_splitting_sim_even_split_slurm.py`
**Even split SLURM script** - Specialized for even split (p=0.5) studies with multiple B values.

**Key features:**
- Auto-generates r values from 1 to B/2+1 for each B
- Each task = (B, seed) combination
- Perfect for comprehensive B/r sweeps

**Usage:**
```bash
# Generate config
python core/leaf_splitting_sim_even_split_slurm.py config \
    --B-min 256 --B-max 512 --B-step 1 \
    --method deferred --seeds 20 \
    --output even_split_config.json

# Collect results
python core/leaf_splitting_sim_even_split_slurm.py collect \
    --results_dir results \
    --output aggregated_results.csv
```

**See:** [USER_GUIDE.md](../USER_GUIDE.md) - Even Split Simulations section

---

### `leaf_splitting_sim_sequence.py`
**Variable batch size simulations** - For time-varying workloads with r_sequence.

**Key features:**
- Supports variable batch sizes (r_sequence)
- Convergence tracking with snapshots
- Long-format CSV output

**Usage:**
```python
from core.leaf_splitting_sim_sequence import simulate_with_r_sequence

result = simulate_with_r_sequence(
    B=240,
    r_sequence=[1, 10, 50, 100, 150, 200],
    repetitions=1000,
    method='immediately',
    p=0.5,
    seed=42
)
```

**See:** [SEQUENCE_GUIDE.md](../SEQUENCE_GUIDE.md) for detailed guide

---

### `leaf_splitting_sim_sequence_slurm.py`
**SLURM for sequence simulations** - Parallel execution of sequence simulations.

**Usage:**
```bash
python core/leaf_splitting_sim_sequence_slurm.py config \
    --B 240 --method immediately \
    --r-sequence 1 10 50 100 150 200 \
    --repetitions 1000 --seeds 20 \
    --output sequence_config.json
```

**See:** [SEQUENCE_GUIDE.md](../SEQUENCE_GUIDE.md) - SLURM Execution section

---

## Analysis & Comparison Scripts

### `compare_split_strategies_r1.py`
**Compare strategies for r=1** - Compare different splitting strategies for single-element insertions.

**Usage:**
```python
from core.compare_split_strategies_r1 import run_strategy_comparison

strategies = [
    {'name': 'even', 'p': 0.5, 'method': 'deferred', 'rounding': 'floor'},
    {'name': 'uneven', 'p': 0.3, 'method': 'immediately', 'rounding': 'floor'}
]

results = run_strategy_comparison(
    B=240, total_insertions=100000,
    strategies=strategies, seeds=[1, 2, 3, 4, 5]
)
```

**Command line:**
```bash
python core/compare_split_strategies_r1.py --config config.json
```

---

### `compare_split_strategies_r1_slurm.py`
**SLURM version** - Parallel execution of strategy comparisons.

**Usage:**
```bash
python core/compare_split_strategies_r1_slurm.py config \
    --B 240 --total_insertions 100000 \
    --strategies even uneven \
    --seeds 20 --output strategy_config.json
```

---

## Theoretical Analysis Scripts

### `check_even_split_optimal.py`
**Theoretical analysis for even split** - Uses probability distribution evolution to check if even split is optimal.

**Key functions:**
- `step_distribution_float()` - One insertion step with float probabilities
- `expected_fullness_float()` - Compute expected fullness
- `compare_range_incremental_float()` - Compare two initial states over time

**Usage:**
```python
from core.check_even_split_optimal import expected_fullness_float

fullness = expected_fullness_float(
    B=26, init_state=(13, 13), steps=200, eps=1e-20
)
```

**Purpose:** Theoretical validation and comparison of different initial states.

---

### `check_even_split_optimal_matrix.py`
**Matrix-based theoretical analysis** - Uses matrix operations for faster computation.

**Key functions:**
- `build_transition_matrix()` - Build transition matrix
- `compute_expectation_matrix()` - Compute expected fullness using matrices
- `compare_range_matrix()` - Compare states using matrix operations

**Usage:**
```python
from core.check_even_split_optimal_matrix import compute_expectation_matrix

fullness, A, time_avg = compute_expectation_matrix(
    B=26, init_state=(13, 13), steps=200
)
```

**Advantage:** Faster than probability distribution approach for large state spaces.

---

### `find_optimal_split_eigenvector.py`
**Eigenvector analysis** - Find optimal splitting strategy using eigenvector analysis of transition matrix.

**Key functions:**
- `build_transition_matrix()` - Build transition matrix for given split strategy
- `find_steady_state_eigenvector()` - Find steady-state distribution
- `compute_fullness_from_eigenvector()` - Compute fullness from eigenvector
- `find_optimal_split_eigenvector()` - Main function to find optimal strategy

**Usage:**
```python
from core.find_optimal_split_eigenvector import find_optimal_split_eigenvector

result = find_optimal_split_eigenvector(B=240, a=120)
print(f"Steady-state fullness: {result['steady_state_fullness']}")
```

**Purpose:** Theoretical analysis to find optimal split parameters for steady-state behavior.

---

### `simulate_variable_r.py`
**Variable r simulation** - Legacy script for variable batch sizes.

**Note:** This functionality is now better handled by `leaf_splitting_sim_sequence.py`. This script may be deprecated.

---

## Quick Reference

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `leaf_splitting_sim.py` | Core simulation | Direct Python usage, imported by other scripts |
| `leaf_splitting_sim_slurm.py` | Parameter sweeps | Large B/r/p sweeps on SLURM |
| `leaf_splitting_sim_even_split_slurm.py` | Even split sweeps | Multiple B values with even split |
| `leaf_splitting_sim_sequence.py` | Variable batch sizes | Time-varying workloads |
| `leaf_splitting_sim_sequence_slurm.py` | Sequence SLURM | Parallel sequence simulations |
| `compare_split_strategies_r1.py` | Strategy comparison | Compare methods for r=1 |
| `check_even_split_optimal.py` | Theoretical analysis | Validate even split optimality |
| `find_optimal_split_eigenvector.py` | Eigenvector analysis | Find optimal split parameters |

---

## Importing Core Functions

All scripts can be imported as modules:

```python
# Core simulation
from core.leaf_splitting_sim import simulate, simulate_variable_r

# Analysis
from core.compare_split_strategies_r1 import run_strategy_comparison

# Theoretical
from core.check_even_split_optimal import expected_fullness_float
from core.find_optimal_split_eigenvector import find_optimal_split_eigenvector
```

---

## See Also

- [README.md](../README.md) - Project overview
- [USER_GUIDE.md](../USER_GUIDE.md) - Complete user guide
- [SEQUENCE_GUIDE.md](../SEQUENCE_GUIDE.md) - Sequence simulations
- [TECHNICAL_DOCS.md](../TECHNICAL_DOCS.md) - Implementation details

