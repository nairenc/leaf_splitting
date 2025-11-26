"""
SLURM-compatible version of compare_split_strategies_r1.py

This script can run a single task (seed + strategy combination) for SLURM array jobs.
"""

import random
import json
import argparse
import sys
import os
from typing import List, Dict, Tuple, Optional

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.leaf_splitting_sim import simulate
import statistics


def run_single_task(task_id: int, config: Dict) -> Dict:
    """
    Run a single simulation task for SLURM.
    
    Parameters
    ----------
    task_id : int
        Task ID from SLURM_ARRAY_TASK_ID
    config : dict
        Configuration with B, total_insertions, strategies, seeds, etc.
    
    Returns
    -------
    dict
        Result for this task
    """
    B = config['B']
    total_insertions = config['total_insertions']
    strategies = config['strategies']
    seeds = config['seeds']
    r = 1  # Fixed r=1
    
    # Decode task_id: (strategy_idx, seed_idx)
    num_strategies = len(strategies)
    num_seeds = len(seeds)
    
    strategy_idx = task_id // num_seeds
    seed_idx = task_id % num_seeds
    
    if strategy_idx >= num_strategies:
        raise ValueError(f"Task ID {task_id} out of range: strategy_idx={strategy_idx}, num_strategies={num_strategies}")
    
    if seed_idx >= num_seeds:
        raise ValueError(f"Task ID {task_id} out of range: seed_idx={seed_idx}, num_seeds={num_seeds}")
    
    strategy = strategies[strategy_idx]
    seed = seeds[seed_idx]
    
    name = strategy['name']
    p = strategy['p']
    method = strategy.get('method', 'deferred')
    rounding = strategy.get('rounding', 'floor')
    
    # Run simulation with time series tracking
    result = simulate(
        B=B,
        r=r,
        total_insertions=total_insertions,
        method=method,
        p=p,
        rounding=rounding,
        seed=seed,
        track_fullness_curve=True  # Track fullness over time
    )
    
    output = {
        'task_id': task_id,
        'strategy_name': name,
        'strategy_idx': strategy_idx,
        'seed': seed,
        'seed_idx': seed_idx,
        'B': B,
        'r': r,
        'p': p,
        'method': method,
        'rounding': rounding,
        'total_insertions': total_insertions,
        'final_fullness': result['final_fullness'],
        'time_avg_fullness': result['time_avg_fullness'],
    }
    
    # Include time series data if available
    if 'fullness_curve' in result:
        output['fullness_curve'] = result['fullness_curve']
        output['time_avg_fullness_curve'] = result['time_avg_fullness_curve']
        if 'sliding_window_avg_curve' in result:
            output['sliding_window_avg_curve'] = result['sliding_window_avg_curve']
    
    return output


def collect_results(results_dir: str, output_file: str):
    """
    Collect all individual result files and aggregate them.
    
    Parameters
    ----------
    results_dir : str
        Directory containing individual result JSON files
    output_file : str
        Output file for aggregated results
    """
    all_results = []
    
    # Find all result files
    for filename in os.listdir(results_dir):
        if filename.startswith('task_') and filename.endswith('.json'):
            filepath = os.path.join(results_dir, filename)
            with open(filepath, 'r') as f:
                all_results.append(json.load(f))
    
    if not all_results:
        print(f"No results found in {results_dir}")
        return
    
    # Try to get B, total_insertions, and count unique seeds from results
    B_from_results = None
    total_insertions_from_results = None
    unique_seeds = set()
    
    if all_results:
        first_result = all_results[0]
        B_from_results = first_result.get('B')
        total_insertions_from_results = first_result.get('total_insertions')
    
    # Group by strategy
    strategy_results = {}
    has_time_series = False
    for result in all_results:
        # Collect unique seeds
        if 'seed' in result:
            unique_seeds.add(result['seed'])
        name = result['strategy_name']
        if name not in strategy_results:
            strategy_results[name] = {
                'final_fullness': [],
                'time_avg_fullness': [],
                'fullness_curves': [],
                'time_avg_fullness_curves': []
            }
        strategy_results[name]['final_fullness'].append(result['final_fullness'])
        strategy_results[name]['time_avg_fullness'].append(result['time_avg_fullness'])
        
        # Collect time series data if available
        if 'fullness_curve' in result:
            has_time_series = True
            strategy_results[name]['fullness_curves'].append(result['fullness_curve'])
            strategy_results[name]['time_avg_fullness_curves'].append(result['time_avg_fullness_curve'])
            if 'sliding_window_avg_curve' in result:
                if 'sliding_window_avg_curves' not in strategy_results[name]:
                    strategy_results[name]['sliding_window_avg_curves'] = []
                strategy_results[name]['sliding_window_avg_curves'].append(result['sliding_window_avg_curve'])
    
    # Compute statistics
    aggregated = {}
    for name, data in strategy_results.items():
        aggregated[name] = {
            'final_fullness': {
                'mean': statistics.mean(data['final_fullness']),
                'stdev': statistics.stdev(data['final_fullness']) if len(data['final_fullness']) > 1 else 0.0,
                'min': min(data['final_fullness']),
                'max': max(data['final_fullness']),
                'values': data['final_fullness']
            },
            'time_avg_fullness': {
                'mean': statistics.mean(data['time_avg_fullness']),
                'stdev': statistics.stdev(data['time_avg_fullness']) if len(data['time_avg_fullness']) > 1 else 0.0,
                'min': min(data['time_avg_fullness']),
                'max': max(data['time_avg_fullness']),
                'values': data['time_avg_fullness']
            },
            'num_runs': len(data['final_fullness'])
        }
        
        # Compute average time series curves if available
        if data['fullness_curves']:
            # All curves should have the same length (same sampling interval)
            # Find the minimum length to handle any edge cases
            min_length = min(len(curve) for curve in data['fullness_curves'])
            
            # Compute point-wise averages
            avg_fullness_curve = []
            avg_time_avg_fullness_curve = []
            
            for i in range(min_length):
                # Average across all seeds at this time point
                fullness_values = [curve[i] for curve in data['fullness_curves'] if i < len(curve)]
                time_avg_values = [curve[i] for curve in data['time_avg_fullness_curves'] if i < len(curve)]
                
                if fullness_values:
                    avg_fullness_curve.append(statistics.mean(fullness_values))
                if time_avg_values:
                    avg_time_avg_fullness_curve.append(statistics.mean(time_avg_values))
            
            aggregated[name]['fullness_curve'] = avg_fullness_curve
            aggregated[name]['time_avg_fullness_curve'] = avg_time_avg_fullness_curve
            
            # Compute average sliding window curves if available
            if 'sliding_window_avg_curves' in data and data['sliding_window_avg_curves']:
                min_length_sw = min(len(curve) for curve in data['sliding_window_avg_curves'])
                avg_sliding_window_curve = []
                for i in range(min_length_sw):
                    sw_values = [curve[i] for curve in data['sliding_window_avg_curves'] if i < len(curve)]
                    if sw_values:
                        avg_sliding_window_curve.append(statistics.mean(sw_values))
                aggregated[name]['sliding_window_avg_curve'] = avg_sliding_window_curve
    
    # Load config to include in output
    config_file = os.path.join(os.path.dirname(results_dir), 'split_strategy_config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # Use values from results if not in config (results are more reliable)
    B_value = B_from_results or config.get('B')
    total_insertions_value = total_insertions_from_results or config.get('total_insertions')
    num_seeds = len(unique_seeds) if unique_seeds else len(config.get('seeds', []))
    
    output_data = {
        'config': {
            'B': B_value,
            'total_insertions': total_insertions_value,
            'num_seeds': num_seeds
        },
        'results': aggregated,
        'note': 'Time series data contains average curves across all seeds' if has_time_series else None
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Collected {len(all_results)} results from {len(strategy_results)} strategies")
    print(f"Saved aggregated results to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='SLURM-compatible split strategy comparison')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a single task')
    run_parser.add_argument('--config', required=True, help='Configuration JSON file')
    run_parser.add_argument('--task_id', type=int, required=True, help='Task ID from SLURM')
    run_parser.add_argument('--output_dir', default='results', help='Output directory for result files')
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect and aggregate results')
    collect_parser.add_argument('--results_dir', required=True, help='Directory containing result files')
    collect_parser.add_argument('--output', required=True, help='Output file for aggregated results')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        # Load config
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        # Run task
        result = run_single_task(args.task_id, config)
        
        # Save result
        os.makedirs(args.output_dir, exist_ok=True)
        output_file = os.path.join(args.output_dir, f"task_{args.task_id:06d}.json")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Task {args.task_id} completed: {result['strategy_name']} (seed={result['seed']})")
        print(f"  Final fullness: {result['final_fullness']:.8f}")
        print(f"  Time-avg fullness: {result['time_avg_fullness']:.8f}")
        
    elif args.command == 'collect':
        collect_results(args.results_dir, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

