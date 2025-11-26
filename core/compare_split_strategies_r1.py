"""
Compare different splitting strategies for r=1 cases.

This script compares:
1. Even split strategy (p=0.5) - splits blocks evenly
2. Alternative strategies (e.g., uneven splits with different p values)

For each strategy, we run multiple simulations with different seeds and compare:
- Final fullness
- Time-averaged fullness

Can be run with a JSON configuration file or with default parameters.
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


def run_strategy_comparison(
    B: int,
    total_insertions: int,
    strategies: List[Dict[str, any]],
    seeds: List[int],
    verbose: bool = True
) -> Dict:
    """
    Compare multiple splitting strategies for r=1.
    
    Parameters
    ----------
    B : int
        Block capacity
    total_insertions : int
        Total number of elements to insert
    strategies : list of dict
        Each dict should have:
        - 'name': strategy name
        - 'p': split ratio (0.0 to 1.0)
        - 'method': 'deferred', 'immediately', 'adaptive', or 'adaptive2'
        - 'rounding': 'floor', 'ceil', or 'nearest'
    seeds : list of int
        Random seeds for multiple runs
    verbose : bool
        Whether to print progress
    
    Returns
    -------
    dict
        Results with statistics for each strategy
    """
    r = 1  # Fixed r=1 for this comparison
    
    results = {}
    
    for strategy in strategies:
        name = strategy['name']
        p = strategy['p']
        method = strategy.get('method', 'deferred')
        rounding = strategy.get('rounding', 'floor')
        
        if verbose:
            print(f"\n=== Strategy: {name} (p={p}, method={method}) ===")
        
        final_fullness_list = []
        time_avg_fullness_list = []
        time_series_data = []  # Store time series for each run
        
        for seed_idx, seed in enumerate(seeds):
            if verbose and (seed_idx + 1) % 10 == 0:
                print(f"  Running seed {seed_idx + 1}/{len(seeds)}...", end='\r')
            
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
            
            final_fullness_list.append(result['final_fullness'])
            time_avg_fullness_list.append(result['time_avg_fullness'])
            
            # Store time series data if available
            if 'fullness_curve' in result:
                ts_entry = {
                    'seed': seed,
                    'fullness_curve': result['fullness_curve'],
                    'time_avg_fullness_curve': result['time_avg_fullness_curve']
                }
                if 'sliding_window_avg_curve' in result:
                    ts_entry['sliding_window_avg_curve'] = result['sliding_window_avg_curve']
                time_series_data.append(ts_entry)
        
        if verbose:
            print(f"  Completed {len(seeds)} runs")
        
        # Compute statistics
        results[name] = {
            'strategy': strategy,
            'final_fullness': {
                'mean': statistics.mean(final_fullness_list),
                'stdev': statistics.stdev(final_fullness_list) if len(final_fullness_list) > 1 else 0.0,
                'min': min(final_fullness_list),
                'max': max(final_fullness_list),
                'values': final_fullness_list
            },
            'time_avg_fullness': {
                'mean': statistics.mean(time_avg_fullness_list),
                'stdev': statistics.stdev(time_avg_fullness_list) if len(time_avg_fullness_list) > 1 else 0.0,
                'min': min(time_avg_fullness_list),
                'max': max(time_avg_fullness_list),
                'values': time_avg_fullness_list
            },
            'num_runs': len(seeds)
        }
        
        # Compute average time series curves if available
        if time_series_data:
            # All curves should have the same length (same sampling interval)
            # Find the minimum length to handle any edge cases
            min_length = min(len(ts['fullness_curve']) for ts in time_series_data)
            
            # Compute point-wise averages
            avg_fullness_curve = []
            avg_time_avg_fullness_curve = []
            
            for i in range(min_length):
                # Average across all seeds at this time point
                fullness_values = [ts['fullness_curve'][i] for ts in time_series_data if i < len(ts['fullness_curve'])]
                time_avg_values = [ts['time_avg_fullness_curve'][i] for ts in time_series_data if i < len(ts['time_avg_fullness_curve'])]
                
                if fullness_values:
                    avg_fullness_curve.append(statistics.mean(fullness_values))
                if time_avg_values:
                    avg_time_avg_fullness_curve.append(statistics.mean(time_avg_values))
            
            results[name]['fullness_curve'] = avg_fullness_curve
            results[name]['time_avg_fullness_curve'] = avg_time_avg_fullness_curve
            
            # Compute average sliding window curves if available
            if time_series_data and 'sliding_window_avg_curve' in time_series_data[0]:
                min_length_sw = min(len(ts['sliding_window_avg_curve']) for ts in time_series_data 
                                   if 'sliding_window_avg_curve' in ts)
                avg_sliding_window_curve = []
                for i in range(min_length_sw):
                    sw_values = [ts['sliding_window_avg_curve'][i] for ts in time_series_data 
                               if 'sliding_window_avg_curve' in ts and i < len(ts['sliding_window_avg_curve'])]
                    if sw_values:
                        avg_sliding_window_curve.append(statistics.mean(sw_values))
                results[name]['sliding_window_avg_curve'] = avg_sliding_window_curve
    
    return results


def print_comparison(results: Dict, metric: str = 'both'):
    """
    Print comparison results in a readable format.
    
    Parameters
    ----------
    results : dict
        Results from run_strategy_comparison
    metric : str
        'final', 'time_avg', or 'both'
    """
    print("\n" + "="*80)
    print("STRATEGY COMPARISON RESULTS")
    print("="*80)
    
    if metric in ['final', 'both']:
        print("\n--- Final Fullness ---")
        print(f"{'Strategy':<30} {'Mean':<12} {'StdDev':<12} {'Min':<12} {'Max':<12}")
        print("-" * 80)
        
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1]['final_fullness']['mean'],
            reverse=True
        )
        
        for name, data in sorted_results:
            ff = data['final_fullness']
            print(f"{name:<30} {ff['mean']:<12.8f} {ff['stdev']:<12.8f} "
                  f"{ff['min']:<12.8f} {ff['max']:<12.8f}")
    
    if metric in ['time_avg', 'both']:
        print("\n--- Time-Averaged Fullness ---")
        print(f"{'Strategy':<30} {'Mean':<12} {'StdDev':<12} {'Min':<12} {'Max':<12}")
        print("-" * 80)
        
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1]['time_avg_fullness']['mean'],
            reverse=True
        )
        
        for name, data in sorted_results:
            taf = data['time_avg_fullness']
            print(f"{name:<30} {taf['mean']:<12.8f} {taf['stdev']:<12.8f} "
                  f"{taf['min']:<12.8f} {taf['max']:<12.8f}")
    
    # Show relative improvements
    if len(results) >= 2:
        print("\n--- Relative Improvement vs Even Split (p=0.5) ---")
        
        even_split_name = None
        for name in results.keys():
            if 'even' in name.lower() or results[name]['strategy']['p'] == 0.5:
                even_split_name = name
                break
        
        if even_split_name:
            even_ff_mean = results[even_split_name]['final_fullness']['mean']
            even_taf_mean = results[even_split_name]['time_avg_fullness']['mean']
            
            print(f"\nBaseline: {even_split_name}")
            print(f"  Final fullness: {even_ff_mean:.8f}")
            print(f"  Time-avg fullness: {even_taf_mean:.8f}")
            
            print(f"\n{'Strategy':<30} {'Final %':<15} {'Time-Avg %':<15}")
            print("-" * 60)
            
            for name, data in sorted(results.items(), key=lambda x: x[1]['final_fullness']['mean'], reverse=True):
                if name != even_split_name:
                    ff_improve = 100 * (data['final_fullness']['mean'] - even_ff_mean) / even_ff_mean
                    taf_improve = 100 * (data['time_avg_fullness']['mean'] - even_taf_mean) / even_taf_mean
                    print(f"{name:<30} {ff_improve:>+14.4f}% {taf_improve:>+14.4f}%")


def load_config(config_file: str) -> Dict:
    """Load configuration from JSON file."""
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config


def create_default_config() -> Dict:
    """Create a default configuration."""
    return {
        'B': 36,
        'total_insertions': 100000,
        'seeds': [random.randint(1, 1000000) for _ in range(50)],
        'strategies': [
            {
                'name': 'Even Split (p=0.5)',
                'p': 0.5,
                'method': 'deferred',
                'rounding': 'floor'
            },
            {
                'name': 'Uneven Split (p=0.4)',
                'p': 0.4,
                'method': 'deferred',
                'rounding': 'floor'
            },
            {
                'name': 'Uneven Split (p=0.6)',
                'p': 0.6,
                'method': 'deferred',
                'rounding': 'floor'
            },
            {
                'name': 'Uneven Split (p=0.45)',
                'p': 0.45,
                'method': 'deferred',
                'rounding': 'floor'
            },
            {
                'name': 'Uneven Split (p=0.55)',
                'p': 0.55,
                'method': 'deferred',
                'rounding': 'floor'
            },
        ]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Compare different splitting strategies for r=1 cases'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to JSON configuration file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file for results (default: auto-generated)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        print(f"Loading configuration from {args.config}")
        config = load_config(args.config)
    else:
        print("Using default configuration")
        random.seed(42)
        config = create_default_config()
    
    # Extract configuration parameters
    B = config.get('B', 36)
    total_insertions = config.get('total_insertions', 100000)
    seeds = config.get('seeds', [])
    strategies = config.get('strategies', [])
    
    # Validate configuration
    if not seeds:
        print("Warning: No seeds provided in config, generating default seeds")
        random.seed(42)
        seeds = [random.randint(1, 1000000) for _ in range(50)]
    
    if not strategies:
        print("Error: No strategies provided in config")
        sys.exit(1)
    
    print(f"\nComparing {len(strategies)} strategies for r=1")
    print(f"B = {B}, total_insertions = {total_insertions}, num_seeds = {len(seeds)}")
    print("\nStrategies:")
    for s in strategies:
        print(f"  - {s['name']}: p={s['p']}, method={s.get('method', 'deferred')}")
    
    # Run comparison
    results = run_strategy_comparison(
        B=B,
        total_insertions=total_insertions,
        strategies=strategies,
        seeds=seeds,
        verbose=True
    )
    
    # Print results
    print_comparison(results, metric='both')
    
    # Save results to file
    if args.output:
        output_file = args.output
    else:
        output_file = f"split_strategy_comparison_B{B}_r1.json"
    
    # Convert to JSON-serializable format
    output_data = {
        'config': {
            'B': B,
            'total_insertions': total_insertions,
            'num_seeds': len(seeds)
        },
        'results': {}
    }
    
    has_time_series = False
    for name, data in results.items():
        output_data['results'][name] = {
            'strategy': data['strategy'],
            'final_fullness': {
                'mean': data['final_fullness']['mean'],
                'stdev': data['final_fullness']['stdev'],
                'min': data['final_fullness']['min'],
                'max': data['final_fullness']['max']
            },
            'time_avg_fullness': {
                'mean': data['time_avg_fullness']['mean'],
                'stdev': data['time_avg_fullness']['stdev'],
                'min': data['time_avg_fullness']['min'],
                'max': data['time_avg_fullness']['max']
            },
            'num_runs': data['num_runs']
        }
        
        # Include average time series data if available
        if 'fullness_curve' in data:
            output_data['results'][name]['fullness_curve'] = data['fullness_curve']
            output_data['results'][name]['time_avg_fullness_curve'] = data['time_avg_fullness_curve']
            if 'sliding_window_avg_curve' in data:
                output_data['results'][name]['sliding_window_avg_curve'] = data['sliding_window_avg_curve']
            has_time_series = True
    
    # Add note about time series data
    if has_time_series:
        output_data['note'] = 'Time series data contains average curves across all seeds'
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nResults saved to {output_file}")

