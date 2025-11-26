#!/usr/bin/env python3
"""
SLURM-compatible leaf splitting simulation for even split (p=0.5).

Focuses on testing many B values and many r values with even split strategy.
Structure: For each (B, seed) combination, try all r values.
"""

import csv
import os
import sys
import argparse
import json
import numpy as np

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.leaf_splitting_sim import simulate


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
    
    For even split: Each task corresponds to a (B, seed) combination,
    and runs all r values for that combination.
    
    Parameters
    ----------
    task_id : int
        Task ID (typically from SLURM_ARRAY_TASK_ID)
    config : dict
        Configuration with method, B_list, r_list, seeds, etc.
    
    Returns
    -------
    list : result records (one per r value)
    """
    B_list = config['B_list']
    method = config['method']
    seeds = config['seeds']
    p = config.get('p', 0.5)  # Even split by default
    total_insertions = config.get('total_insertions', None)
    insertion_scale = config.get('insertion_scale', 'sqrt')
    base_insertions = config.get('base_insertions', 100_000)
    rounding = config.get('rounding', 'floor')
    r_step = config.get('r_step', 1)  # Step size for r values
    
    # Calculate which (B, seed) combination
    total_B = len(B_list)
    seed_idx = task_id // total_B
    B_idx = task_id % total_B
    
    if seed_idx >= len(seeds):
        raise ValueError(f"Task ID {task_id} out of range")
    
    seed = seeds[seed_idx]
    B = B_list[B_idx]
    
    # Generate r values for this B: 1 to B/2+1
    r_max = B // 2 + 1
    r_list = list(range(1, r_max + 1, r_step))
    
    # Run simulations for all r values
    results = []
    
    for r in r_list:
            
        # Calculate total insertions for this r
        if insertion_scale == 'sqrt':
            import math
            total_ins = int((math.sqrt(r) + 1) * base_insertions)
        elif insertion_scale == 'linear':
            total_ins = r * base_insertions
        else:  # 'fixed'
            total_ins = total_insertions if total_insertions else base_insertions
        
        alpha = r / B
        
        # Run simulation
        result = simulate(
            B=B, r=r, total_insertions=total_ins, method=method, p=p,
            rounding=rounding, seed=seed
        )
        
        results.append({
            "task_id": task_id,
            "B": B,
            "r": r,
            "alpha": alpha,
            "p": p,
            "seed": seed,
            "fullness": result["final_fullness"],
            "time_avg_fullness": result["time_avg_fullness"],
        })
    
    return results


def generate_config(
    B_list=None,
    method='deferred',
    p=0.5,
    r_step=1,
    total_insertions=None,
    insertion_scale='sqrt',
    base_insertions=100_000,
    rounding='floor',
    seeds_count=20,
    seeds_method="seedsequence",
    seeds_master=2025,
    config_file="even_split_config.json"
):
    """
    Generate a configuration file for SLURM array jobs.
    
    Structure: For each (B, seed) combination, try r values from 1 to B/2+1.
    p is fixed at 0.5 (even split).
    
    Parameters
    ----------
    B_list : list of int
        List of B values to test
    method : str
        Splitting method ('deferred', 'immediately', 'adaptive', etc.)
    p : float
        Split ratio (default 0.5 for even split)
    r_step : int
        Step size for r values (default 1, meaning all r values from 1 to B/2+1)
    total_insertions : int
        Fixed total insertions (if insertion_scale='fixed')
    insertion_scale : str
        'sqrt', 'linear', or 'fixed'
    base_insertions : int
        Base insertions for sqrt/linear scale
    rounding : str
        'floor', 'ceil', or 'nearest'
    seeds_count : int
        Number of random seeds
    seeds_method : str
        Seed generation method
    seeds_master : int
        Master seed for reproducibility
    config_file : str
        Output config filename
    """
    if B_list is None:
        B_list = [60, 120, 240, 480]
    else:
        B_list = list(B_list)
    
    seeds = gen_seeds(count=seeds_count, method=seeds_method, master_seed=seeds_master)
    
    config = {
        'B_list': B_list,
        'method': method,
        'p': p,
        'r_step': r_step,
        'seeds': seeds,
        'insertion_scale': insertion_scale,
        'base_insertions': base_insertions,
        'rounding': rounding,
    }
    
    # Add total_insertions only if using fixed scale
    if insertion_scale == 'fixed' and total_insertions is not None:
        config['total_insertions'] = total_insertions
    
    total_tasks = len(seeds) * len(B_list)
    
    # Calculate r ranges for each B
    r_ranges = {}
    for B in B_list:
        r_max = B // 2 + 1
        r_count = len(list(range(1, r_max + 1, r_step)))
        r_ranges[B] = (1, r_max, r_count)
    
    print(f"Configuration saved to {config_file}")
    print(f"Method: {method}")
    print(f"Split ratio (p): {p} (even split)")
    print(f"B values: {len(B_list)} values")
    print(f"  {B_list}")
    print(f"r values: Auto-generated per B (1 to B/2+1, step={r_step})")
    for B, (r_min, r_max, r_count) in sorted(r_ranges.items()):
        print(f"  B={B}: r from {r_min} to {r_max} ({r_count} values)")
    print(f"Seeds: {len(seeds)} seeds")
    print(f"\nTask structure:")
    print(f"  Each task = (B, seed) combination")
    print(f"  Each task runs r values from 1 to B/2+1")
    print(f"  Total tasks: {total_tasks}")
    print(f"    {len(seeds)} seeds × {len(B_list)} B values")
    
    print(f"\nInsertion strategy: {insertion_scale}")
    if insertion_scale == 'sqrt':
        import math
        # Show range for smallest and largest B
        B_min, B_max = min(B_list), max(B_list)
        r_min_small = 1
        r_max_small = B_min // 2 + 1
        r_min_large = 1
        r_max_large = B_max // 2 + 1
        ins_min = int((math.sqrt(r_min_small) + 1) * base_insertions)
        ins_max = int((math.sqrt(r_max_large) + 1) * base_insertions)
        print(f"  Base: {base_insertions:,}, Range: {ins_min:,} to {ins_max:,} insertions")
        print(f"  Formula: (sqrt(r) + 1) × {base_insertions:,}")
    elif insertion_scale == 'linear':
        print(f"  Total insertions = r × {base_insertions:,}")
    else:  # fixed
        print(f"  Fixed total insertions: {total_insertions:,} (same for all r values)")
    
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
        If True (default), aggregate results by (B, r) combination across seeds.
        If False, keep all individual seed results.
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
                for key in ['task_id', 'B', 'r', 'seed']:
                    if key in row and row[key]:
                        row[key] = int(row[key])
                for key in ['alpha', 'p', 'fullness', 'time_avg_fullness']:
                    if key in row and row[key]:
                        row[key] = float(row[key])
                all_rows.append(row)
    
    print(f"Collected {len(all_rows)} raw results")
    
    if aggregate:
        # Aggregate results by (B, r) across seeds
        print(f"Aggregating results by (B, r) across seeds...")
        grouped = defaultdict(list)
        
        for row in all_rows:
            key = (row['B'], row['r'], row['alpha'], row['p'])
            grouped[key].append({
                'fullness': row['fullness'],
                'time_avg_fullness': row['time_avg_fullness']
            })
        
        print(f"Found {len(grouped)} unique (B, r) combinations")
        
        # Compute statistics for each group
        aggregated_rows = []
        for (B, r, alpha, p), results in sorted(grouped.items()):
            fullness_values = [res['fullness'] for res in results]
            time_avg_fullness_values = [res['time_avg_fullness'] for res in results]
            
            aggregated_rows.append({
                'B': B,
                'r': r,
                'alpha': alpha,
                'p': p,
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
            'B', 'r', 'alpha', 'p',
            'fullness_mean', 'fullness_std', 'fullness_min', 'fullness_max',
            'time_avg_fullness_mean', 'time_avg_fullness_std', 'time_avg_fullness_min', 'time_avg_fullness_max',
            'n_seeds'
        ]
        
        with open(output_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(aggregated_rows)
        
        print(f"Saved {len(aggregated_rows)} aggregated results to {output_csv}")
        print(f"Reduced from {len(all_rows)} rows to {len(aggregated_rows)} rows")
    else:
        # Write all individual results (per-seed format)
        fieldnames = ['task_id', 'B', 'r', 'alpha', 'p', 'seed', 'fullness', 'time_avg_fullness']
        
        with open(output_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        
        print(f"Saved {len(all_rows)} per-seed results to {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Even split leaf splitting simulation for SLURM")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a single task')
    run_parser.add_argument('--config', required=True, help='Configuration JSON file')
    run_parser.add_argument('--task_id', type=int, required=True, help='Task ID')
    run_parser.add_argument('--output_dir', default='results', help='Output directory for result files')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Generate configuration file')
    config_parser.add_argument('--B', type=int, nargs='+', help='B values (e.g., --B 60 120 240 480)')
    config_parser.add_argument('--B-min', type=int, help='Minimum B value')
    config_parser.add_argument('--B-max', type=int, help='Maximum B value')
    config_parser.add_argument('--B-step', type=int, default=60, help='Step for B values')
    config_parser.add_argument('--method', default='deferred', 
                               choices=['deferred', 'immediately', 'adaptive', 'adaptive2', 'phased'],
                               help='Splitting method')
    config_parser.add_argument('--r-step', type=int, default=1, 
                               help='Step for r values (r values are auto-generated from 1 to B/2+1)')
    config_parser.add_argument('--p', type=float, default=0.5, help='Split ratio (default 0.5 for even split)')
    config_parser.add_argument('--insertion_scale', default='sqrt', choices=['sqrt', 'linear', 'fixed'],
                               help='Insertion scaling strategy')
    config_parser.add_argument('--base_insertions', type=int, default=100_000,
                               help='Base insertions for sqrt/linear scale')
    config_parser.add_argument('--total_insertions', type=int, help='Total insertions (for fixed scale)')
    config_parser.add_argument('--rounding', default='floor', choices=['floor', 'ceil', 'nearest'],
                               help='Split rounding mode')
    config_parser.add_argument('--seeds', type=int, default=20, help='Number of seeds')
    config_parser.add_argument('--output', default='even_split_config.json', help='Output config file')
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect and aggregate results into single CSV')
    collect_parser.add_argument('--results_dir', required=True, help='Directory with result_*.csv files')
    collect_parser.add_argument('--output', required=True, help='Output CSV file')
    collect_parser.add_argument('--no-aggregate', action='store_true', 
                               help='Keep per-seed results instead of aggregating')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        # Load config
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        # Run task
        result = run_single_task(args.task_id, config)
        
        # Write result
        results_to_write = result if isinstance(result, list) else [result]
        
        # Create output directory and filename
        os.makedirs(args.output_dir, exist_ok=True)
        output_file = os.path.join(args.output_dir, f"result_{args.task_id:06d}.csv")
        
        with open(output_file, 'w', newline='') as f:
            fieldnames = ['task_id', 'B', 'r', 'alpha', 'p', 'seed', 'fullness', 'time_avg_fullness']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results_to_write)
        
        print(f"Task {args.task_id} completed, wrote {len(results_to_write)} results to {output_file}")
    
    elif args.command == 'config':
        # Generate B_list
        if args.B:
            B_list = args.B
        elif args.B_min and args.B_max:
            B_list = list(range(args.B_min, args.B_max + 1, args.B_step))
        else:
            # Default B values
            B_list = [60, 120, 240, 480]
        
        generate_config(
            B_list=B_list,
            method=args.method,
            p=args.p,
            r_step=args.r_step,
            total_insertions=args.total_insertions,
            insertion_scale=args.insertion_scale,
            base_insertions=args.base_insertions,
            rounding=args.rounding,
            seeds_count=args.seeds,
            config_file=args.output
        )
    
    elif args.command == 'collect':
        aggregate = not args.no_aggregate  # Aggregate by default unless --no-aggregate is specified
        collect_results(args.results_dir, args.output, aggregate=aggregate)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

