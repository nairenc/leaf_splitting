#!/usr/bin/env python3
"""
SLURM-compatible unified leaf splitting simulation.

Supports both 'deferred' and 'immediately' splitting methods.
Compatible with SLURM array jobs for parallel execution.
"""

import csv
import os
import sys
import argparse
import json
import numpy as np
from leaf_splitting_sim import simulate


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
        Task ID (typically from SLURM_ARRAY_TASK_ID)
    config : dict
        Configuration with method, B, r_list, p_list, seeds, etc.
    
    Returns
    -------
    dict or list : result record(s)
    
    Notes
    -----
    batch_by_r: true → r is FIXED per task, runs all p values
    batch_by_p: true → p is FIXED per task, runs all r values
    """
    batch_by_r = config.get('batch_by_r', True)  # Default
    batch_by_p = config.get('batch_by_p', False)
    
    if batch_by_r:
        return run_task_batch_by_r(task_id, config)
    elif batch_by_p:
        return run_task_batch_by_p(task_id, config)
    else:
        return run_task_single_combination(task_id, config)


def run_task_single_combination(task_id, config):
    """Run a single (seed, r, p) combination."""
    B = config['B']
    method = config['method']
    r_list = config['r_list']
    p_list = config['p_list']
    seeds = config['seeds']
    total_insertions = config.get('total_insertions', None)
    insertion_scale = config.get('insertion_scale', 'fixed')
    base_insertions = config.get('base_insertions', 100_000)
    rounding = config.get('rounding', 'floor')
    
    # Decode task_id
    total_r = len(r_list)
    total_p = len(p_list)
    
    seed_idx = task_id // (total_r * total_p)
    remainder = task_id % (total_r * total_p)
    r_idx = remainder // total_p
    p_idx = remainder % total_p
    
    if seed_idx >= len(seeds):
        raise ValueError(f"Task ID {task_id} out of range")
    
    sd = seeds[seed_idx]
    r = r_list[r_idx]
    p_val = p_list[p_idx]
    
    # Calculate total insertions based on scale
    if insertion_scale == 'sqrt':
        import math
        total_ins = int((math.sqrt(r) + 1) * base_insertions)
    elif insertion_scale == 'linear':
        total_ins = r * base_insertions
    else:  # 'fixed'
        total_ins = total_insertions if total_insertions else base_insertions
    
    # Run simulation
    result = simulate(
        B=B, r=r, total_insertions=total_ins, method=method, p=p_val, 
        rounding=rounding, seed=sd
    )
    
    alpha = r / B
    
    return {
        "task_id": task_id,
        "B": B,
        "r": r,
        "alpha": alpha,
        "p": p_val,
        "seed": sd,
        "fullness": result["final_fullness"],
        "time_avg_fullness": result["time_avg_fullness"],
    }


def run_task_batch_by_r(task_id, config):
    """Run all p values for a single (seed, r) combination - r is FIXED."""
    B = config['B']
    method = config['method']
    r_list = config['r_list']
    p_list = config['p_list']
    seeds = config['seeds']
    total_insertions = config.get('total_insertions', None)
    insertion_scale = config.get('insertion_scale', 'fixed')
    base_insertions = config.get('base_insertions', 100_000)
    rounding = config.get('rounding', 'floor')
    
    # Calculate which (seed, r) combination
    total_r = len(r_list)
    seed_idx = task_id // total_r
    r_idx = task_id % total_r
    
    if seed_idx >= len(seeds):
        raise ValueError(f"Task ID {task_id} out of range")
    
    sd = seeds[seed_idx]
    r = r_list[r_idx]
    
    # Calculate total insertions
    if insertion_scale == 'sqrt':
        import math
        total_ins = int((math.sqrt(r) + 1) * base_insertions)
    elif insertion_scale == 'linear':
        total_ins = r * base_insertions
    else:  # 'fixed'
        total_ins = total_insertions if total_insertions else base_insertions
    
    # Run simulations for all p values
    results = []
    alpha = r / B
    
    for p_val in p_list:
        result = simulate(
            B=B, r=r, total_insertions=total_ins, method=method, p=p_val,
            rounding=rounding, seed=sd
        )
        
        results.append({
            "task_id": task_id,
            "B": B,
            "r": r,
            "alpha": alpha,
            "p": p_val,
            "seed": sd,
            "fullness": result["final_fullness"],
            "time_avg_fullness": result["time_avg_fullness"],
        })
    
    return results


def run_task_batch_by_p(task_id, config):
    """Run all r values for a single (seed, p) combination - p is FIXED."""
    B = config['B']
    method = config['method']
    r_list = config['r_list']
    p_list = config['p_list']
    seeds = config['seeds']
    total_insertions = config.get('total_insertions', None)
    insertion_scale = config.get('insertion_scale', 'fixed')
    base_insertions = config.get('base_insertions', 100_000)
    rounding = config.get('rounding', 'floor')
    
    # Calculate which (seed, p) combination
    total_p = len(p_list)
    seed_idx = task_id // total_p
    p_idx = task_id % total_p
    
    if seed_idx >= len(seeds):
        raise ValueError(f"Task ID {task_id} out of range")
    
    sd = seeds[seed_idx]
    p_val = p_list[p_idx]
    
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
        result = simulate(
            B=B, r=r, total_insertions=total_ins, method=method, p=p_val,
            rounding=rounding, seed=sd
        )
        
        results.append({
            "task_id": task_id,
            "B": B,
            "r": r,
            "alpha": alpha,
            "p": p_val,
            "seed": sd,
            "fullness": result["final_fullness"],
            "time_avg_fullness": result["time_avg_fullness"],
        })
    
    return results


def generate_config(
    B=256,
    method='deferred',
    r_list=None,
    p=0.5,
    total_insertions=None,
    insertion_scale='sqrt',
    base_insertions=100_000,
    rounding='floor',
    seeds_count=20,
    seeds_method="seedsequence",
    seeds_master=2025,
    batch_by_r=True,
    batch_by_p=False,
    config_file="sweep_config.json"
):
    """Generate a configuration file for SLURM array jobs."""
    
    if r_list is None:
        r_list = list(range(1, B, 4))
    else:
        r_list = list(r_list)
    
    if isinstance(p, (int, float)):
        p_list = [p]
    else:
        p_list = list(p)
    
    seeds = gen_seeds(count=seeds_count, method=seeds_method, master_seed=seeds_master)
    
    config = {
        'B': B,
        'method': method,
        'r_list': r_list,
        'p_list': p_list,
        'seeds': seeds,
        'insertion_scale': insertion_scale,
        'base_insertions': base_insertions,
        'rounding': rounding,
        'batch_by_r': batch_by_r,
        'batch_by_p': batch_by_p,
    }
    
    # Add total_insertions only if using fixed scale
    if insertion_scale == 'fixed' and total_insertions is not None:
        config['total_insertions'] = total_insertions
    
    if batch_by_r:
        total_tasks = len(seeds) * len(r_list)
        print(f"Configuration saved to {config_file}")
        print(f"Method: {method}")
        print(f"Batch mode (by r): Each task FIXES r, runs all {len(p_list)} p values")
        print(f"Total tasks: {total_tasks}")
        print(f"  {len(seeds)} seeds × {len(r_list)} r values")
        print(f"  Each task runs {len(p_list)} p values internally")
    elif batch_by_p:
        total_tasks = len(seeds) * len(p_list)
        print(f"Configuration saved to {config_file}")
        print(f"Method: {method}")
        print(f"Batch mode (by p): Each task FIXES p, runs all {len(r_list)} r values")
        print(f"Total tasks: {total_tasks}")
        print(f"  {len(seeds)} seeds × {len(p_list)} p values")
        print(f"  Each task runs {len(r_list)} r values internally")
    else:
        total_tasks = len(seeds) * len(r_list) * len(p_list)
        print(f"Configuration saved to {config_file}")
        print(f"Method: {method}")
        print(f"Total tasks: {total_tasks}")
        print(f"  {len(seeds)} seeds × {len(r_list)} r values × {len(p_list)} p values")
    
    print(f"\nInsertion strategy: {insertion_scale}")
    if insertion_scale == 'sqrt':
        import math
        r_min, r_max = min(r_list), max(r_list)
        ins_min = int((math.sqrt(r_min) + 1) * base_insertions)
        ins_max = int((math.sqrt(r_max) + 1) * base_insertions)
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


def aggregate_results_by_rp(input_csv, output_csv):
    """
    Aggregate results by (r, p) combination across all seeds.
    
    Computes mean, std, min, max, and count for fullness metrics.
    
    Parameters
    ----------
    input_csv : str
        Input CSV file with individual seed results
    output_csv : str
        Output CSV file with aggregated results
    """
    from collections import defaultdict
    
    print(f"Reading results from {input_csv}...")
    
    # Group results by (B, r, alpha, p)
    grouped = defaultdict(list)
    
    with open(input_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            B = int(row['B'])
            r = int(row['r'])
            alpha = float(row['alpha'])
            p = float(row['p'])
            fullness = float(row['fullness'])
            time_avg_fullness = float(row['time_avg_fullness'])
            
            key = (B, r, alpha, p)
            grouped[key].append({
                'fullness': fullness,
                'time_avg_fullness': time_avg_fullness
            })
    
    print(f"Found {len(grouped)} unique (B, r, p) combinations")
    print(f"Aggregating results across seeds...")
    
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
    
    print(f"Aggregated {len(aggregated_rows)} (r, p) combinations")
    print(f"Reduced from {sum(len(v) for v in grouped.values())} rows to {len(aggregated_rows)} rows")
    print(f"Results saved to {output_csv}")


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
        If True (default), aggregate results by (r, p) combination across seeds.
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
        # Aggregate results by (B, r, alpha, p)
        print(f"Aggregating results by (r, p) across seeds...")
        grouped = defaultdict(list)
        
        for row in all_rows:
            key = (row['B'], row['r'], row['alpha'], row['p'])
            grouped[key].append({
                'fullness': row['fullness'],
                'time_avg_fullness': row['time_avg_fullness']
            })
        
        print(f"Found {len(grouped)} unique (B, r, p) combinations")
        
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
    parser = argparse.ArgumentParser(description="Unified leaf splitting simulation for SLURM")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a single task')
    run_parser.add_argument('--config', required=True, help='Configuration JSON file')
    run_parser.add_argument('--task_id', type=int, required=True, help='Task ID')
    run_parser.add_argument('--output_dir', default='results', help='Output directory for result files')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Generate configuration file')
    config_parser.add_argument('--B', type=int, default=256, help='Block capacity')
    config_parser.add_argument('--method', default='deferred', choices=['deferred', 'immediately', 'adaptive', 'adaptive2'],
                               help='Splitting method')
    config_parser.add_argument('--r_min', type=int, default=1, help='Minimum r value')
    config_parser.add_argument('--r_max', type=int, help='Maximum r value (default: B-1)')
    config_parser.add_argument('--r_step', type=int, default=1, help='Step for r values')
    config_parser.add_argument('--p_min', type=float, default=0.1, help='Minimum p value')
    config_parser.add_argument('--p_max', type=float, default=0.5, help='Maximum p value')
    config_parser.add_argument('--p_count', type=int, default=40, help='Number of p values')
    config_parser.add_argument('--insertion_scale', default='sqrt', choices=['sqrt', 'linear', 'fixed'],
                               help='Insertion scaling strategy')
    config_parser.add_argument('--base_insertions', type=int, default=100_000,
                               help='Base insertions for sqrt/linear scale')
    config_parser.add_argument('--total_insertions', type=int, help='Total insertions (for fixed scale)')
    config_parser.add_argument('--rounding', default='floor', choices=['floor', 'ceil', 'nearest'],
                               help='Split rounding mode')
    config_parser.add_argument('--seeds', type=int, default=20, help='Number of seeds')
    config_parser.add_argument('--batch_by_r', action='store_true', help='Batch by r (fix r, vary p)')
    config_parser.add_argument('--batch_by_p', action='store_true', help='Batch by p (fix p, vary r)')
    config_parser.add_argument('--output', default='sweep_config.json', help='Output config file')
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect and aggregate results into single CSV')
    collect_parser.add_argument('--results_dir', required=True, help='Directory with result_*.csv files')
    collect_parser.add_argument('--output', required=True, help='Output CSV file')
    collect_parser.add_argument('--no-aggregate', action='store_true', 
                               help='Keep per-seed results instead of aggregating (not recommended for large datasets)')
    
    # Aggregate command
    aggregate_parser = subparsers.add_parser('aggregate', help='Aggregate results by (r, p) across seeds')
    aggregate_parser.add_argument('--input', required=True, help='Input CSV file with all results')
    aggregate_parser.add_argument('--output', required=True, help='Output aggregated CSV file')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        # Load config
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        # Run task
        result = run_single_task(args.task_id, config)
        
        # Write result
        is_list = isinstance(result, list)
        results_to_write = result if is_list else [result]
        
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
        # Generate r_list
        r_max = args.r_max if args.r_max else args.B - 1
        r_list = list(range(args.r_min, r_max + 1, args.r_step))
        
        # Generate p_list
        p_list = list(np.linspace(args.p_min, args.p_max, args.p_count))
        
        # Determine batching mode
        batch_by_r = args.batch_by_r
        batch_by_p = args.batch_by_p
        if not batch_by_r and not batch_by_p:
            batch_by_r = True  # Default
        
        generate_config(
            B=args.B,
            method=args.method,
            r_list=r_list,
            p=p_list,
            total_insertions=args.total_insertions,
            insertion_scale=args.insertion_scale,
            base_insertions=args.base_insertions,
            rounding=args.rounding,
            seeds_count=args.seeds,
            batch_by_r=batch_by_r,
            batch_by_p=batch_by_p,
            config_file=args.output
        )
    
    elif args.command == 'collect':
        aggregate = not args.no_aggregate  # Aggregate by default unless --no-aggregate is specified
        collect_results(args.results_dir, args.output, aggregate=aggregate)
    
    elif args.command == 'aggregate':
        aggregate_results_by_rp(args.input, args.output)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

