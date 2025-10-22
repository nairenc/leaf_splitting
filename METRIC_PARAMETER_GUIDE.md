# Fullness Metric Parameter Guide

## Overview

The analysis scripts now support choosing between two fullness metrics:

1. **Time-averaged fullness** (default, `--metric time_avg`)
2. **Final fullness** (`--metric final`)

## Why Two Metrics?

### Time-Averaged Fullness
- **What it is**: Cumulative average of fullness over all batches
- **Formula**: `∑(total_keys × batch_size) / ∑(total_capacity × batch_size)`
- **Properties**:
  - More stable (lower variance across seeds)
  - Better matches theoretical predictions (e.g., ln(2) for r=1, p=0.5)
  - Represents steady-state behavior
  - **Recommended for comparing methods**

### Final Fullness
- **What it is**: Snapshot fullness at the end of simulation
- **Formula**: `final_keys / (B × final_blocks)`
- **Properties**:
  - Higher variance (stochastic fluctuations)
  - May not be at steady state for finite runs
  - Shows end-state of the system
  - Useful for understanding transient behavior

## Example: r=1, p=0.5 (Theory: ln(2) = 0.693)

| Insertions | Final Fullness | Time-Avg Fullness |
|------------|----------------|-------------------|
| 100k       | 0.760          | 0.692             |
| 2M         | 0.682          | 0.697             |
| 16M        | 0.684          | 0.695             |
| Theory     | ~0.693 (limit) | 0.693             |

**Observation**: Time-averaged fullness (0.695) is closer to theory (0.693) than final fullness (0.684).

## Usage

### Basic Analysis (default: time-averaged)

```bash
python analyze/analyze_results.py --input results.csv
```

Generates plots with time-averaged fullness (more stable, matches theory).

### Using Final Fullness

```bash
python analyze/analyze_results.py --input results.csv --metric final
```

Generates plots with final snapshot fullness.

### Filtered Analysis

```bash
# Time-averaged (default)
python analyze/analyze_results_filtered.py --input results.csv --r 0.5 1.0

# Final fullness
python analyze/analyze_results_filtered.py --input results.csv --r 0.5 1.0 --metric final
```

## Output Files

Filenames reflect which metric was used:

**Time-averaged** (default):
- `B240_r1-240_p0.11-0.90_maxp_timeavg_fullness_vs_alpha.png`
- `B240_r1-240_p0.11-0.90_minr_timeavg_fullness_vs_p.png`

**Final**:
- `B240_r1-240_p0.11-0.90_maxp_final_fullness_vs_alpha.png`
- `B240_r1-240_p0.11-0.90_minr_final_fullness_vs_p.png`

## Recommendation

**For scientific analysis and method comparison**:
- Use `--metric time_avg` (default)
- More stable, lower variance
- Better matches theoretical predictions
- Represents true steady-state behavior

**For understanding end-state**:
- Use `--metric final`
- Shows the final snapshot
- Useful for validating convergence
- May have more variance

## Data Columns

Both metrics are always computed and saved in result CSVs:
- `fullness`: Final snapshot fullness
- `time_avg_fullness`: Time-averaged fullness (cumulative average)

The `--metric` parameter only affects which column is used for plotting.


