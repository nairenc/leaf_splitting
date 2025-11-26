#!/usr/bin/env python3
"""
SLURM-compatible leaf splitting simulation with variable batch sizes (r_sequence).

This script enables parallel execution of sequence simulations across different seeds
using SLURM array jobs. Compatible with leaf_splitting_sim_sequence.py.
"""

import csv
import os
import sys
import argparse
import json
import numpy as np

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.leaf_splitting_sim_sequence import simulate_with_r_sequence


def gen_seeds(count=50, method="seedsequence", master_seed=2025):
    """Generate a list of integer RNG seeds."""
    if count <= 0:
        return []

    if method == "seedsequence":
        ss = np.random.SeedSequence(master_seed)
        children = ss.spawn(count)
        return [
            int(np.random.default_rng(c).integers(0, 2**32 - 1, dtype=np.uint32))
            for c in children
        ]
    elif method == "rng":
        rng = np.random.default_rng(master_seed)
        return [int(x) for x in rng.integers(0, 2**32 - 1, size=count, dtype=np.uint32)]
    elif method == "urandom":
        return [int.from_bytes(os.urandom(4), "little") for _ in range(count)]
    else:
        raise ValueError("Unknown method; choose from {'seedsequence','rng','urandom'}.")


def run_single_task(task_id, config):
    """
    Run a single simulation task based on task_id and config.
    
    Parameters
    ----------
    task_id : int
        Task ID (typically from SLURM_ARRAY_TASK_ID), corresponds to seed index
    config : dict
        Configuration with B, r_sequence, method, p, repetitions, seeds, etc.
    
    Returns
    -------
    dict : result record with time series data
    """
    B = config['B']
    method = config['method']
    r_sequence = config['r_sequence']
    p = config.get('p', 0.5)
    repetitions = config.get('repetitions', 1)
    rounding = config.get('rounding', 'floor')
    num_snapshots = config.get('num_snapshots', 100)
    seeds = config['seeds']
    
    # Get seed for this task
    if task_id >= len(seeds):
        raise ValueError(f"Task ID {task_id} out of range (only {len(seeds)} seeds available)")
    
    seed = seeds[task_id]
    
    # Run simulation
    result = simulate_with_r_sequence(
        B=B,
        r_sequence=r_sequence,
        method=method,
        p=p,
        rounding=rounding,
        repetitions=repetitions,
        seed=seed,
        num_snapshots=num_snapshots
    )
    
    # Calculate mean alpha for reporting
    mean_alpha = sum(r_sequence) / len(r_sequence) / B
    
    return {
        "task_id": task_id,
        "seed": seed,
        "B": B,
        "method": method,
        "p": p,
        "r_sequence": r_sequence,
        "repetitions": repetitions,
        "sequence_length": len(r_sequence),
        "mean_alpha": mean_alpha,
        "total_insertions": result["total_insertions"],
        "total_splits": result["total_splits"],
        "split_rate": result["total_splits"] / result["total_insertions"] if result["total_insertions"] > 0 else 0.0,
        "final_blocks": result["final_blocks"],
        "final_fullness": result["final_fullness"],
        "time_avg_fullness": result["time_avg_fullness"],
        # Time series data
        "fullness_snapshots": result["fullness_snapshots"],
        "time_avg_fullness_snapshots": result["time_avg_fullness_snapshots"],
        "repetition_points": result["repetition_points"],
        "num_snapshots": result["num_snapshots"],
    }


def generate_config(
    B=240,
    method='immediately',
    r_sequence=None,
    p=0.5,
    repetitions=1000,
    rounding='floor',
    seeds_count=20,
    seeds_method="seedsequence",
    seeds_master=2025,
    config_file="sequence_sweep_config.json"
):
    """Generate a configuration file for SLURM array jobs."""
    
    if r_sequence is None:
        r_sequence = [1, 10, 50, 100, 150]
    else:
        r_sequence = list(r_sequence)
    
    seeds = gen_seeds(count=seeds_count, method=seeds_method, master_seed=seeds_master)
    
    config = {
        'B': B,
        'method': method,
        'r_sequence': r_sequence,
        'p': p,
        'repetitions': repetitions,
        'rounding': rounding,
        'seeds': seeds,
    }
    
    total_tasks = len(seeds)
    
    print(f"Configuration saved to {config_file}")
    print(f"Method: {method}")
    print(f"Block capacity (B): {B}")
    print(f"Split ratio (p): {p}")
    print(f"r_sequence: {r_sequence}")
    print(f"Repetitions of sequence: {repetitions}")
    print(f"Total tasks (seeds): {total_tasks}")
    print(f"\nEach task will:")
    print(f"  - Use a different random seed")
    print(f"  - Run the same r_sequence {repetitions} times")
    print(f"  - Perform {sum(r_sequence) * repetitions:,} total insertions")
    
    mean_r = sum(r_sequence) / len(r_sequence)
    mean_alpha = mean_r / B
    print(f"\nSequence statistics:")
    print(f"  - Sequence length: {len(r_sequence)}")
    print(f"  - Mean r: {mean_r:.2f}")
    print(f"  - Mean alpha (r/B): {mean_alpha:.4f}")
    print(f"  - Min r: {min(r_sequence)}")
    print(f"  - Max r: {max(r_sequence)}")
    
    print(f"\nUse SLURM array job: #SBATCH --array=0-{total_tasks-1}")
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_file, total_tasks


def collect_results(results_dir, output_csv, aggregate=True):
    """
    Collect all task results into a single CSV file.
    
    Parameters
    ----------
    results_dir : str
        Directory containing result_*.csv files
    output_csv : str
        Output CSV filename
    aggregate : bool
        If True, compute statistics across seeds for each repetition.
        If False, keep individual seed data.
    """
    import glob
    from collections import defaultdict
    
    result_files = sorted(glob.glob(os.path.join(results_dir, "result_*.csv")))
    
    if not result_files:
        print(f"No result files found in {results_dir}")
        return
    
    print(f"Collecting {len(result_files)} result files...")
    
    all_rows = []
    
    for fname in result_files:
        with open(fname, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric columns
                for key in ['task_id', 'B', 'seed', 'total_insertions', 'total_splits', 'final_blocks', 'repetition']:
                    if key in row and row[key]:
                        row[key] = int(row[key])
                for key in ['p', 'mean_alpha', 'split_rate', 'fullness', 'time_avg_fullness']:
                    if key in row and row[key]:
                        row[key] = float(row[key])
                all_rows.append(row)
    
    print(f"Collected {len(all_rows)} snapshot rows from {len(result_files)} tasks")
    
    if aggregate:
        # Aggregate results across seeds for each repetition point
        print(f"Aggregating results across seeds...")
        
        # Group by (B, method, p, repetition)
        grouped = defaultdict(list)
        
        for row in all_rows:
            key = (row['B'], row['method'], row['p'], row['repetition'])
            grouped[key].append({
                'fullness': row['fullness'],
                'time_avg_fullness': row['time_avg_fullness'],
            })
        
        # Get common metadata from first row
        first_row = all_rows[0]
        
        # Compute statistics for each repetition point
        aggregated_rows = []
        for (B, method, p, repetition), results in sorted(grouped.items()):
            fullness_values = [res['fullness'] for res in results]
            time_avg_fullness_values = [res['time_avg_fullness'] for res in results]
            
            aggregated_rows.append({
                'B': B,
                'method': method,
                'p': p,
                'mean_alpha': first_row['mean_alpha'],
                'repetition': repetition,
                'fullness_mean': np.mean(fullness_values),
                'fullness_std': np.std(fullness_values, ddof=1) if len(fullness_values) > 1 else 0.0,
                'fullness_min': np.min(fullness_values),
                'fullness_max': np.max(fullness_values),
                'time_avg_fullness_mean': np.mean(time_avg_fullness_values),
                'time_avg_fullness_std': np.std(time_avg_fullness_values, ddof=1) if len(time_avg_fullness_values) > 1 else 0.0,
                'time_avg_fullness_min': np.min(time_avg_fullness_values),
                'time_avg_fullness_max': np.max(time_avg_fullness_values),
                'n_seeds': len(results)
            })
        
        # Write aggregated results
        fieldnames = [
            'B', 'method', 'p', 'mean_alpha', 'repetition',
            'fullness_mean', 'fullness_std', 'fullness_min', 'fullness_max',
            'time_avg_fullness_mean', 'time_avg_fullness_std', 'time_avg_fullness_min', 'time_avg_fullness_max',
            'n_seeds'
        ]
        
        with open(output_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(aggregated_rows)
        
        print(f"Saved {len(aggregated_rows)} aggregated time points to {output_csv}")
        print(f"Aggregated across {len(result_files)} seeds")
    else:
        # Write all individual results
        fieldnames = ['task_id', 'seed', 'B', 'method', 'p', 'mean_alpha',
                     'total_insertions', 'total_splits', 'split_rate', 'final_blocks',
                     'repetition', 'fullness', 'time_avg_fullness']
        
        with open(output_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        
        print(f"Saved {len(all_rows)} individual snapshot rows to {output_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="SLURM-compatible sequence simulation with variable batch sizes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate configuration
  python leaf_splitting_sim_sequence_slurm.py config --B 240 --method immediately --p 0.5 \\
      --r-sequence 1 10 50 100 150 --repetitions 1000 --seeds 20

  # Run a single task (called by SLURM)
  python leaf_splitting_sim_sequence_slurm.py run --config sequence_sweep_config.json \\
      --task_id $SLURM_ARRAY_TASK_ID --output_dir results

  # Collect results
  python leaf_splitting_sim_sequence_slurm.py collect --results_dir results \\
      --output aggregated_results.csv
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a single task')
    run_parser.add_argument('--config', required=True, help='Configuration JSON file')
    run_parser.add_argument('--task_id', type=int, required=True, help='Task ID (seed index)')
    run_parser.add_argument('--output_dir', default='results', help='Output directory for result files')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Generate configuration file')
    config_parser.add_argument('--B', type=int, default=240, help='Block capacity')
    config_parser.add_argument('--method', default='immediately', 
                               choices=['deferred', 'immediately', 'adaptive', 'adaptive2'],
                               help='Splitting method')
    config_parser.add_argument('--r-sequence', '--r_sequence', nargs='+', type=int, required=True,
                               help='Sequence of batch sizes, e.g., --r-sequence 1 10 50 100')
    config_parser.add_argument('--p', type=float, default=0.5, help='Split ratio')
    config_parser.add_argument('--repetitions', type=int, default=1000,
                               help='Number of times to repeat r_sequence')
    config_parser.add_argument('--rounding', default='floor', choices=['floor', 'ceil', 'nearest'],
                               help='Split rounding mode')
    config_parser.add_argument('--seeds', type=int, default=20, help='Number of seeds')
    config_parser.add_argument('--seeds_method', default='seedsequence',
                               choices=['seedsequence', 'rng', 'urandom'],
                               help='Method for generating seeds')
    config_parser.add_argument('--seeds_master', type=int, default=2025,
                               help='Master seed for seed generation')
    config_parser.add_argument('--output', default='sequence_sweep_config.json', 
                               help='Output config file')
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect results into single CSV')
    collect_parser.add_argument('--results_dir', required=True, help='Directory with result_*.csv files')
    collect_parser.add_argument('--output', required=True, help='Output CSV file')
    collect_parser.add_argument('--no-aggregate', action='store_true',
                               help='Keep per-seed results instead of aggregating across seeds for each repetition')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        # Load config
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        # Run task
        result = run_single_task(args.task_id, config)
        
        # Create output directory and filename
        os.makedirs(args.output_dir, exist_ok=True)
        output_file = os.path.join(args.output_dir, f"result_{args.task_id:06d}.csv")
        
        # Write result in long format (one row per snapshot)
        fieldnames = ['task_id', 'seed', 'B', 'method', 'p', 'mean_alpha', 
                     'total_insertions', 'total_splits', 'split_rate', 'final_blocks',
                     'repetition', 'fullness', 'time_avg_fullness']
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write one row per snapshot
            for rep, fullness, time_avg in zip(
                result['repetition_points'],
                result['fullness_snapshots'],
                result['time_avg_fullness_snapshots']
            ):
                writer.writerow({
                    'task_id': result['task_id'],
                    'seed': result['seed'],
                    'B': result['B'],
                    'method': result['method'],
                    'p': result['p'],
                    'mean_alpha': result['mean_alpha'],
                    'total_insertions': result['total_insertions'],
                    'total_splits': result['total_splits'],
                    'split_rate': result['split_rate'],
                    'final_blocks': result['final_blocks'],
                    'repetition': rep,
                    'fullness': fullness,
                    'time_avg_fullness': time_avg
                })
        
        print(f"Task {args.task_id} completed, wrote {len(result['repetition_points'])} snapshots to {output_file}")
    
    elif args.command == 'config':
        generate_config(
            B=args.B,
            method=args.method,
            r_sequence=args.r_sequence,
            p=args.p,
            repetitions=args.repetitions,
            rounding=args.rounding,
            seeds_count=args.seeds,
            seeds_method=args.seeds_method,
            seeds_master=args.seeds_master,
            config_file=args.output
        )
    
    elif args.command == 'collect':
        aggregate = not args.no_aggregate
        collect_results(args.results_dir, args.output, aggregate=aggregate)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

