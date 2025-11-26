"""
Analyze and visualize results from compare_split_strategies_r1_slurm.py

This script loads the aggregated JSON results and creates visualizations:
1. Bar chart comparing final fullness and time-averaged fullness across strategies
2. Time series plots showing how fullness evolves over time for each strategy
"""

import json
import argparse
import os
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional


def load_results(json_file: str) -> Dict:
    """Load aggregated results from JSON file."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data


def plot_strategy_comparison(results: Dict, save_dir: Optional[str] = None, json_file: Optional[str] = None):
    """
    Plot bar chart comparing strategies.
    
    Parameters
    ----------
    results : dict
        Results dictionary from loaded JSON
    save_dir : str or None
        Directory to save figures (if None, uses directory of JSON file)
    json_file : str or None
        Path to JSON file (used to determine default save_dir)
    """
    strategies = results['results']
    config = results['config']
    
    strategy_names = list(strategies.keys())
    final_fullness_means = [strategies[name]['final_fullness']['mean'] for name in strategy_names]
    final_fullness_stds = [strategies[name]['final_fullness']['stdev'] for name in strategy_names]
    time_avg_fullness_means = [strategies[name]['time_avg_fullness']['mean'] for name in strategy_names]
    time_avg_fullness_stds = [strategies[name]['time_avg_fullness']['stdev'] for name in strategy_names]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    x = np.arange(len(strategy_names))
    width = 0.35
    
    # Plot final fullness
    bars1 = ax1.bar(x - width/2, final_fullness_means, width, 
                    yerr=final_fullness_stds, label='Final Fullness', 
                    capsize=5, alpha=0.8)
    ax1.set_xlabel('Strategy', fontsize=12)
    ax1.set_ylabel('Final Fullness', fontsize=12)
    ax1.set_title(f'Final Fullness Comparison\nB={config["B"]}, {config["num_seeds"]} seeds', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(strategy_names, rotation=45, ha='right')
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.legend()
    
    # Add value labels on bars
    for i, (bar, mean, std) in enumerate(zip(bars1, final_fullness_means, final_fullness_stds)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + std + 0.01,
                f'{mean:.4f}', ha='center', va='bottom', fontsize=9)
    
    # Plot time-averaged fullness
    bars2 = ax2.bar(x - width/2, time_avg_fullness_means, width,
                    yerr=time_avg_fullness_stds, label='Time-Avg Fullness',
                    capsize=5, alpha=0.8, color='orange')
    ax2.set_xlabel('Strategy', fontsize=12)
    ax2.set_ylabel('Time-Averaged Fullness', fontsize=12)
    ax2.set_title(f'Time-Averaged Fullness Comparison\nB={config["B"]}, {config["num_seeds"]} seeds', fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(strategy_names, rotation=45, ha='right')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.legend()
    
    # Add value labels on bars
    for i, (bar, mean, std) in enumerate(zip(bars2, time_avg_fullness_means, time_avg_fullness_stds)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + std + 0.01,
                f'{mean:.4f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    if save_dir is None:
        save_dir = os.path.dirname(os.path.abspath(json_file)) if json_file else '.'
    os.makedirs(save_dir, exist_ok=True)
    
    filename = os.path.join(save_dir, 'strategy_comparison.png')
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved comparison plot: {filename}")
    
    plt.show()


def plot_time_series(results: Dict, save_dir: Optional[str] = None, json_file: Optional[str] = None):
    """
    Plot time series curves showing how fullness evolves over time.
    
    Parameters
    ----------
    results : dict
        Results dictionary from loaded JSON
    save_dir : str or None
        Directory to save figures (if None, uses directory of JSON file)
    json_file : str or None
        Path to JSON file (used to determine default save_dir)
    """
    strategies = results['results']
    config = results['config']
    
    # Check if time series data is available
    has_time_series = any('fullness_curve' in strategies[name] for name in strategies.keys())
    
    if not has_time_series:
        print("No time series data available in results.")
        return
    
    # Check if sliding window data is available
    has_sliding_window = any('sliding_window_avg_curve' in strategies[name] for name in strategies.keys())
    
    if has_sliding_window:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14))
    else:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Get B from config, or try to get it from results directory
    B = config.get('B')
    if B is None:
        # Try to load from config file if available
        if json_file:
            config_file = os.path.join(os.path.dirname(json_file), 'split_strategy_config.json')
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        file_config = json.load(f)
                        B = file_config.get('B')
                except:
                    pass
    
    if B is None:
        raise ValueError("B (block capacity) not found in config. Please ensure the config file contains 'B'.")
    
    # Calculate sample interval (B // 3)
    sample_interval = max(1, B // 3)
    total_insertions = config.get('total_insertions')
    if total_insertions is None:
        raise ValueError("total_insertions not found in config.")
    r = 1  # Fixed r=1 for this comparison
    
    # Create x-axis (insertion counts)
    # Each point represents sample_interval batches
    num_batches = total_insertions // r
    sampled_batches = [i for i in range(0, num_batches, sample_interval)]
    if sampled_batches[-1] != num_batches - 1:
        sampled_batches.append(num_batches - 1)
    
    # Convert to insertion counts
    insertion_counts = [batch_idx * r for batch_idx in sampled_batches]
    
    # Plot instantaneous fullness curves
    for name, data in strategies.items():
        if 'fullness_curve' in data:
            curve = data['fullness_curve']
            # Truncate to match available data points
            x_data = insertion_counts[:len(curve)]
            y_data = curve
            ax1.plot(x_data, y_data, marker='o', markersize=3, label=name, linewidth=1.5, alpha=0.8)
    
    ax1.set_xlabel('Total Insertions', fontsize=12)
    ax1.set_ylabel('Instantaneous Fullness', fontsize=12)
    ax1.set_title(f'Fullness Evolution Over Time\nB={B}, r=1, sampled every {sample_interval} batches', fontsize=12)
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(left=0)
    
    # Plot time-averaged fullness curves
    for name, data in strategies.items():
        if 'time_avg_fullness_curve' in data:
            curve = data['time_avg_fullness_curve']
            # Truncate to match available data points
            x_data = insertion_counts[:len(curve)]
            y_data = curve
            ax2.plot(x_data, y_data, marker='o', markersize=3, label=name, linewidth=1.5, alpha=0.8)
    
    ax2.set_xlabel('Total Insertions', fontsize=12)
    ax2.set_ylabel('Time-Averaged Fullness', fontsize=12)
    ax2.set_title(f'Time-Averaged Fullness Evolution Over Time\nB={B}, r=1, sampled every {sample_interval} batches', fontsize=12)
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(left=0)
    
    # Plot sliding window average fullness curves (if available)
    if has_sliding_window:
        for name, data in strategies.items():
            if 'sliding_window_avg_curve' in data:
                curve = data['sliding_window_avg_curve']
                # Truncate to match available data points
                x_data = insertion_counts[:len(curve)]
                y_data = curve
                ax3.plot(x_data, y_data, marker='o', markersize=3, label=name, linewidth=1.5, alpha=0.8)
        
        ax3.set_xlabel('Total Insertions', fontsize=12)
        ax3.set_ylabel('Sliding Window Avg Fullness', fontsize=12)
        ax3.set_title(f'Sliding Window Average Fullness (Last 10B insertions)\nB={B}, r=1, sampled every {sample_interval} batches', fontsize=12)
        ax3.legend(loc='best')
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim(left=0)
    
    plt.tight_layout()
    
    if save_dir is None:
        save_dir = os.path.dirname(os.path.abspath(json_file)) if json_file else '.'
    os.makedirs(save_dir, exist_ok=True)
    
    filename = os.path.join(save_dir, 'time_series_fullness.png')
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved time series plot: {filename}")
    
    plt.show()


def analyze_last_20_percent(results: Dict, metric: str = 'both'):
    """
    Analyze which strategy performs best in the last 20% of the simulation.
    
    Parameters
    ----------
    results : dict
        Results dictionary from loaded JSON
    metric : str
        'instantaneous', 'time_avg', 'sliding_window', or 'both' (includes all)
    
    Returns
    -------
    dict
        Statistics about which strategy wins in the last 20%
    """
    strategies = results['results']
    
    # Check if time series data is available
    has_time_series = any('fullness_curve' in strategies[name] for name in strategies.keys())
    
    if not has_time_series:
        print("No time series data available for last 20% analysis.")
        return None
    
    stats = {}
    
    if metric in ['instantaneous', 'both']:
        # Analyze instantaneous fullness
        instantaneous_wins = {name: 0 for name in strategies.keys() if 'fullness_curve' in strategies[name]}
        
        # Get all curves and find the minimum length
        curves = {name: strategies[name]['fullness_curve'] 
                 for name in strategies.keys() if 'fullness_curve' in strategies[name]}
        
        if curves:
            min_length = min(len(curve) for curve in curves.values())
            last_20_percent_start = int(min_length * 0.8)
            
            # For each time point in the last 20%, find the best strategy
            for i in range(last_20_percent_start, min_length):
                best_strategy = None
                best_value = -1
                
                for name, curve in curves.items():
                    if i < len(curve) and curve[i] > best_value:
                        best_value = curve[i]
                        best_strategy = name
                
                if best_strategy:
                    instantaneous_wins[best_strategy] += 1
            
            stats['instantaneous'] = {
                'wins': instantaneous_wins,
                'total_points': min_length - last_20_percent_start,
                'percentage': {name: (wins / (min_length - last_20_percent_start) * 100) 
                              for name, wins in instantaneous_wins.items()}
            }
    
    if metric in ['time_avg', 'both']:
        # Analyze time-averaged fullness
        time_avg_wins = {name: 0 for name in strategies.keys() 
                        if 'time_avg_fullness_curve' in strategies[name]}
        
        # Get all curves and find the minimum length
        curves = {name: strategies[name]['time_avg_fullness_curve'] 
                 for name in strategies.keys() 
                 if 'time_avg_fullness_curve' in strategies[name]}
        
        if curves:
            min_length = min(len(curve) for curve in curves.values())
            last_20_percent_start = int(min_length * 0.8)
            
            # For each time point in the last 20%, find the best strategy
            for i in range(last_20_percent_start, min_length):
                best_strategy = None
                best_value = -1
                
                for name, curve in curves.items():
                    if i < len(curve) and curve[i] > best_value:
                        best_value = curve[i]
                        best_strategy = name
                
                if best_strategy:
                    time_avg_wins[best_strategy] += 1
            
            stats['time_avg'] = {
                'wins': time_avg_wins,
                'total_points': min_length - last_20_percent_start,
                'percentage': {name: (wins / (min_length - last_20_percent_start) * 100) 
                              for name, wins in time_avg_wins.items()}
            }
    
    if metric in ['sliding_window', 'both']:
        # Analyze sliding window average fullness
        sliding_window_wins = {name: 0 for name in strategies.keys() 
                              if 'sliding_window_avg_curve' in strategies[name]}
        
        # Get all curves and find the minimum length
        curves = {name: strategies[name]['sliding_window_avg_curve'] 
                 for name in strategies.keys() 
                 if 'sliding_window_avg_curve' in strategies[name]}
        
        if curves:
            min_length = min(len(curve) for curve in curves.values())
            last_20_percent_start = int(min_length * 0.8)
            
            # For each time point in the last 20%, find the best strategy
            for i in range(last_20_percent_start, min_length):
                best_strategy = None
                best_value = -1
                
                for name, curve in curves.items():
                    if i < len(curve) and curve[i] > best_value:
                        best_value = curve[i]
                        best_strategy = name
                
                if best_strategy:
                    sliding_window_wins[best_strategy] += 1
            
            stats['sliding_window'] = {
                'wins': sliding_window_wins,
                'total_points': min_length - last_20_percent_start,
                'percentage': {name: (wins / (min_length - last_20_percent_start) * 100) 
                              for name, wins in sliding_window_wins.items()}
            }
    
    return stats


def find_top_differences(results: Dict, metric: str = 'sliding_window', top_n: int = 20, output_dir: str = None):
    """
    Find the top N moments where even split outperforms others most, 
    and where other strategies outperform even split most.
    
    Parameters
    ----------
    results : dict
        Results dictionary from loaded JSON
    metric : str
        'instantaneous', 'time_avg', 'sliding_window'
    top_n : int
        Number of top differences to find (default: 20)
    output_dir : str
        Directory to save output file
    
    Returns
    -------
    dict
        Top differences analysis results
    """
    strategies = results['results']
    config = results['config']
    
    # Identify even split strategy (name contains "even" or "Even", or p=0.5)
    even_split_name = None
    for name in strategies.keys():
        name_lower = name.lower()
        # Check name first
        if 'even' in name_lower:
            even_split_name = name
            break
        # Check strategy data for p=0.5
        strategy_data = strategies[name].get('strategy', {})
        if isinstance(strategy_data, dict) and strategy_data.get('p') == 0.5:
            # Make sure it's not phased (phased also uses p=0.5 initially)
            if 'phased' not in name_lower:
                even_split_name = name
                break
    
    if not even_split_name:
        print("Warning: Could not identify even split strategy. Looking for strategy with p=0.5...")
        for name, data in strategies.items():
            strategy_data = data.get('strategy', {})
            if isinstance(strategy_data, dict) and strategy_data.get('p') == 0.5:
                if 'phased' not in name.lower():
                    even_split_name = name
                    break
    
    if not even_split_name:
        print("Error: Could not find even split strategy in results.")
        return None
    
    print(f"\nIdentified even split strategy: {even_split_name}")
    
    # Get the curve for the selected metric
    curve_key_map = {
        'instantaneous': 'fullness_curve',
        'time_avg': 'time_avg_fullness_curve',
        'sliding_window': 'sliding_window_avg_curve'
    }
    
    curve_key = curve_key_map.get(metric, 'sliding_window_avg_curve')
    
    if curve_key not in strategies[even_split_name]:
        print(f"Error: {curve_key} not found in even split strategy data.")
        return None
    
    even_split_curve = strategies[even_split_name][curve_key]
    
    # Get other strategies' curves
    other_strategies = {}
    for name, data in strategies.items():
        if name != even_split_name and curve_key in data:
            other_strategies[name] = data[curve_key]
    
    if not other_strategies:
        print("Error: No other strategies found with time series data.")
        return None
    
    # Find minimum length across all curves
    all_curves = [even_split_curve] + list(other_strategies.values())
    min_length = min(len(curve) for curve in all_curves)
    
    # Calculate differences at each time point
    differences = []
    
    for i in range(min_length):
        even_value = even_split_curve[i]
        
        # Compare with each other strategy
        for other_name, other_curve in other_strategies.items():
            other_value = other_curve[i]
            diff = even_value - other_value  # Positive means even split is better
            
            differences.append({
                'time_index': i,
                'even_split': even_split_name,
                'other_strategy': other_name,
                'even_value': even_value,
                'other_value': other_value,
                'difference': diff,
                'even_better': diff > 0
            })
    
    # Sort by difference magnitude
    even_better = sorted([d for d in differences if d['even_better']], 
                        key=lambda x: x['difference'], reverse=True)[:top_n]
    other_better = sorted([d for d in differences if not d['even_better']], 
                         key=lambda x: abs(x['difference']), reverse=True)[:top_n]
    
    # Calculate insertion counts for time indices
    B = config.get('B')
    if B is None:
        B = 240  # Default fallback
    sample_interval = max(1, B // 3)
    total_insertions = config.get('total_insertions', 1000000)
    r = 1
    num_batches = total_insertions // r
    sampled_batches = [i for i in range(0, num_batches, sample_interval)]
    if sampled_batches[-1] != num_batches - 1:
        sampled_batches.append(num_batches - 1)
    insertion_counts = [batch_idx * r for batch_idx in sampled_batches]
    
    # Add insertion counts to results
    for item in even_better + other_better:
        if item['time_index'] < len(insertion_counts):
            item['insertion_count'] = insertion_counts[item['time_index']]
        else:
            item['insertion_count'] = None
    
    result = {
        'metric': metric,
        'even_split_strategy': even_split_name,
        'top_even_better': even_better,
        'top_other_better': other_better
    }
    
    # Don't save individual files here - will be saved together in main function
    return result


def print_last_20_percent_analysis(stats: Dict):
    """
    Print the last 20% analysis results in a readable format.
    
    Parameters
    ----------
    stats : dict
        Statistics from analyze_last_20_percent
    """
    if not stats:
        return
    
    print("\n" + "="*80)
    print("LAST 20% PERFORMANCE ANALYSIS")
    print("="*80)
    
    if 'instantaneous' in stats:
        print("\n--- Instantaneous Fullness (Last 20%) ---")
        inst_stats = stats['instantaneous']
        print(f"Total data points analyzed: {inst_stats['total_points']}")
        print(f"\n{'Strategy':<40} {'Wins':<10} {'Percentage':<15}")
        print("-" * 65)
        
        # Sort by wins (descending)
        sorted_wins = sorted(inst_stats['wins'].items(), key=lambda x: x[1], reverse=True)
        for name, wins in sorted_wins:
            percentage = inst_stats['percentage'][name]
            print(f"{name:<40} {wins:<10} {percentage:>14.2f}%")
    
    if 'time_avg' in stats:
        print("\n--- Time-Averaged Fullness (Last 20%) ---")
        ta_stats = stats['time_avg']
        print(f"Total data points analyzed: {ta_stats['total_points']}")
        print(f"\n{'Strategy':<40} {'Wins':<10} {'Percentage':<15}")
        print("-" * 65)
        
        # Sort by wins (descending)
        sorted_wins = sorted(ta_stats['wins'].items(), key=lambda x: x[1], reverse=True)
        for name, wins in sorted_wins:
            percentage = ta_stats['percentage'][name]
            print(f"{name:<40} {wins:<10} {percentage:>14.2f}%")
    
    if 'sliding_window' in stats:
        print("\n--- Sliding Window Average Fullness (Last 20%) ---")
        sw_stats = stats['sliding_window']
        print(f"Total data points analyzed: {sw_stats['total_points']}")
        print(f"Window size: 10*B insertions")
        print(f"\n{'Strategy':<40} {'Wins':<10} {'Percentage':<15}")
        print("-" * 65)
        
        # Sort by wins (descending)
        sorted_wins = sorted(sw_stats['wins'].items(), key=lambda x: x[1], reverse=True)
        for name, wins in sorted_wins:
            percentage = sw_stats['percentage'][name]
            print(f"{name:<40} {wins:<10} {percentage:>14.2f}%")


def plot_combined_comparison(results: Dict, save_dir: Optional[str] = None, json_file: Optional[str] = None):
    """
    Create a combined plot showing both metrics side by side.
    
    Parameters
    ----------
    results : dict
        Results dictionary from loaded JSON
    save_dir : str or None
        Directory to save figures
    json_file : str or None
        Path to JSON file (used to determine default save_dir)
    """
    strategies = results['results']
    config = results['config']
    
    strategy_names = list(strategies.keys())
    final_fullness_means = [strategies[name]['final_fullness']['mean'] for name in strategy_names]
    time_avg_fullness_means = [strategies[name]['time_avg_fullness']['mean'] for name in strategy_names]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(strategy_names))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, final_fullness_means, width, label='Final Fullness', alpha=0.8)
    bars2 = ax.bar(x + width/2, time_avg_fullness_means, width, label='Time-Avg Fullness', alpha=0.8, color='orange')
    
    ax.set_xlabel('Strategy', fontsize=12)
    ax.set_ylabel('Fullness', fontsize=12)
    ax.set_title(f'Strategy Comparison\nB={config["B"]}, Total Insertions={config["total_insertions"]}, {config["num_seeds"]} seeds', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(strategy_names, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.005,
                   f'{height:.4f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    if save_dir is None:
        save_dir = os.path.dirname(os.path.abspath(json_file)) if json_file else '.'
    os.makedirs(save_dir, exist_ok=True)
    
    filename = os.path.join(save_dir, 'combined_comparison.png')
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved combined comparison plot: {filename}")
    
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description='Analyze and visualize strategy comparison results'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to aggregated results JSON file'
    )
    parser.add_argument(
        '--plots',
        type=str,
        nargs='+',
        choices=['comparison', 'time_series', 'combined', 'all'],
        default=['all'],
        help='Which plots to generate (default: all)'
    )
    
    args = parser.parse_args()
    
    # Load results
    print(f"Loading results from {args.input}...")
    results = load_results(args.input)
    
    # Output directory is same as input file directory
    output_dir = os.path.dirname(os.path.abspath(args.input))
    
    print(f"Found {len(results['results'])} strategies")
    print(f"Configuration: B={results['config']['B']}, "
          f"total_insertions={results['config']['total_insertions']}, "
          f"num_seeds={results['config']['num_seeds']}")
    
    # Analyze last 20% performance
    print("\n" + "="*80)
    print("ANALYZING LAST 20% PERFORMANCE")
    print("="*80)
    last_20_stats = analyze_last_20_percent(results, metric='both')
    if last_20_stats:
        print_last_20_percent_analysis(last_20_stats)
    
    # Find top differences
    print("\n" + "="*80)
    print("FINDING TOP 20 DIFFERENCES")
    print("="*80)
    
    all_top_diffs = {}
    for metric in ['instantaneous', 'time_avg', 'sliding_window']:
        print(f"\nAnalyzing {metric} metric...")
        top_diffs = find_top_differences(results, metric=metric, top_n=20, output_dir=None)  # Don't save individual files
        if top_diffs:
            all_top_diffs[metric] = top_diffs
            print(f"  Found {len(top_diffs['top_even_better'])} moments where even split is better")
            print(f"  Found {len(top_diffs['top_other_better'])} moments where other strategies are better")
    
    # Save all results to a single text file
    if all_top_diffs:
        txt_file = os.path.join(output_dir, 'top_20_differences.txt')
        with open(txt_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("TOP 20 DIFFERENCES ANALYSIS\n")
            f.write("="*80 + "\n\n")
            
            for metric, top_diffs in all_top_diffs.items():
                f.write(f"\n{'='*80}\n")
                f.write(f"METRIC: {metric.upper()}\n")
                f.write(f"{'='*80}\n")
                f.write(f"Even Split Strategy: {top_diffs['even_split_strategy']}\n\n")
                
                f.write(f"TOP 20 MOMENTS WHERE EVEN SPLIT OUTPERFORMS OTHERS:\n")
                f.write("-"*80 + "\n")
                f.write(f"{'Rank':<6} {'Time Index':<12} {'Insertions':<15} {'Even Value':<15} {'Other Strategy':<30} {'Other Value':<15} {'Difference':<15}\n")
                f.write("-"*80 + "\n")
                for rank, item in enumerate(top_diffs['top_even_better'], 1):
                    f.write(f"{rank:<6} {item['time_index']:<12} {item.get('insertion_count', 'N/A'):<15} "
                           f"{item['even_value']:<15.8f} {item['other_strategy']:<30} "
                           f"{item['other_value']:<15.8f} {item['difference']:<15.8f}\n")
                
                f.write(f"\n\nTOP 20 MOMENTS WHERE OTHER STRATEGIES OUTPERFORM EVEN SPLIT:\n")
                f.write("-"*80 + "\n")
                f.write(f"{'Rank':<6} {'Time Index':<12} {'Insertions':<15} {'Even Value':<15} {'Other Strategy':<30} {'Other Value':<15} {'Difference':<15}\n")
                f.write("-"*80 + "\n")
                for rank, item in enumerate(top_diffs['top_other_better'], 1):
                    f.write(f"{rank:<6} {item['time_index']:<12} {item.get('insertion_count', 'N/A'):<15} "
                           f"{item['even_value']:<15.8f} {item['other_strategy']:<30} "
                           f"{item['other_value']:<15.8f} {item['difference']:<15.8f}\n")
                f.write("\n")
        
        print(f"\nSaved all top differences analysis to: {txt_file}")
        
        # Also save JSON for all metrics
        json_file = os.path.join(output_dir, 'top_20_differences.json')
        with open(json_file, 'w') as f:
            json.dump(all_top_diffs, f, indent=2)
        print(f"Saved JSON data to: {json_file}")
    
    # Generate plots
    plots_to_generate = args.plots
    if 'all' in plots_to_generate:
        plots_to_generate = ['comparison', 'time_series', 'combined']
    
    if 'comparison' in plots_to_generate:
        print("\nGenerating strategy comparison plot...")
        plot_strategy_comparison(results, output_dir, args.input)
    
    if 'time_series' in plots_to_generate:
        print("\nGenerating time series plots...")
        plot_time_series(results, output_dir, args.input)
    
    if 'combined' in plots_to_generate:
        print("\nGenerating combined comparison plot...")
        plot_combined_comparison(results, output_dir, args.input)
    
    print(f"\nFigures saved to: {output_dir}")
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()

