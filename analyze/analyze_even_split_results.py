"""
analyze_even_split_results.py
Load and visualize even split (p=0.5) simulation results.
Plots fullness vs r (or alpha) for each B value, with optional B filtering.
"""

import csv
import argparse
import os


def load_results_from_csv(filename='aggregated_results.csv'):
    """Load the CSV data and return as list of dictionaries.
    
    Works with aggregated even split results.
    Expects columns: B, r, alpha, p, fullness_mean, time_avg_fullness_mean, etc.
    """
    records = []
    
    with open(filename, 'r', newline='') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            record = {
                'B': int(row['B']),
                'r': int(row['r']),
                'alpha': float(row['alpha']),
                'p': float(row['p']),
            }
            
            # Load aggregated statistics
            if 'fullness_mean' in row:
                record['fullness'] = float(row['fullness_mean'])
                record['fullness_std'] = float(row.get('fullness_std', 0))
                record['fullness_min'] = float(row.get('fullness_min', record['fullness']))
                record['fullness_max'] = float(row.get('fullness_max', record['fullness']))
            else:
                # Fallback if only single values
                record['fullness'] = float(row.get('fullness', 0))
                record['fullness_std'] = 0
                record['fullness_min'] = record['fullness']
                record['fullness_max'] = record['fullness']
            
            if 'time_avg_fullness_mean' in row:
                record['time_avg_fullness'] = float(row['time_avg_fullness_mean'])
                record['time_avg_fullness_std'] = float(row.get('time_avg_fullness_std', 0))
                record['time_avg_fullness_min'] = float(row.get('time_avg_fullness_min', record['time_avg_fullness']))
                record['time_avg_fullness_max'] = float(row.get('time_avg_fullness_max', record['time_avg_fullness']))
            else:
                # Fallback
                record['time_avg_fullness'] = float(row.get('time_avg_fullness', record['fullness']))
                record['time_avg_fullness_std'] = 0
                record['time_avg_fullness_min'] = record['time_avg_fullness']
                record['time_avg_fullness_max'] = record['time_avg_fullness']
            
            record['n_seeds'] = int(row.get('n_seeds', 1))
            records.append(record)
    
    print(f"Loaded {len(records)} records from {filename}")
    return records


def plot_by_B(records, B_values=None, save_dir=None, metric='time_avg', show_range=True, x_axis='alpha'):
    """
    Plot fullness vs r (or alpha) for each B value.
    
    Parameters
    ----------
    records : list
        Data records
    B_values : list of int or None
        List of B values to plot (if None, plots all B values)
    save_dir : str or None
        Directory to save figures
    metric : str
        Which fullness metric: 'time_avg' (default) or 'final'
    show_range : bool
        If True, show min/max range as shaded area
    x_axis : str
        'alpha' (r/B) or 'r' (absolute r values)
    """
    import matplotlib.pyplot as plt
    
    if len(records) == 0:
        print("No records to plot!")
        return
    
    # Get unique B values
    all_B_values = sorted(list(dict.fromkeys([r['B'] for r in records])))
    
    if B_values is None:
        B_values = all_B_values
    else:
        # Filter to only B values that exist in data
        B_values = [B for B in B_values if B in all_B_values]
        if not B_values:
            print(f"Error: None of the specified B values {B_values} are in the data!")
            print(f"Available B values: {all_B_values}")
            return
    
    print(f"Plotting for B values: {B_values}")
    
    # Determine which fullness metric to use
    fullness_key = 'time_avg_fullness' if metric == 'time_avg' else 'fullness'
    fullness_min_key = fullness_key + '_min'
    fullness_max_key = fullness_key + '_max'
    fullness_std_key = fullness_key + '_std'
    metric_label = 'time-averaged fullness' if metric == 'time_avg' else 'final fullness'
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot each B value
    for B in B_values:
        # Filter records for this B
        B_records = [r for r in records if r['B'] == B]
        B_records = sorted(B_records, key=lambda x: x['r'])
        
        if not B_records:
            continue
        
        # Extract data
        if x_axis == 'alpha':
            x_vals = [r['alpha'] for r in B_records]
            x_label = 'α = r / B'
        else:
            x_vals = [r['r'] for r in B_records]
            x_label = 'r (batch size)'
        
        y_vals = [r[fullness_key] for r in B_records]
        y_min = [r[fullness_min_key] for r in B_records]
        y_max = [r[fullness_max_key] for r in B_records]
        y_std = [r[fullness_std_key] for r in B_records]
        
        # Plot main curve
        ax.plot(x_vals, y_vals, marker='o', markersize=4, linewidth=2, 
                label=f'B={B}', alpha=0.8)
        
        # Show range (min/max or std)
        if show_range:
            if any(y_max[i] > y_min[i] for i in range(len(y_vals))):
                # Use min/max if available
                ax.fill_between(x_vals, y_min, y_max, alpha=0.2)
            elif any(s > 0 for s in y_std):
                # Fallback to std
                ax.fill_between(x_vals,
                               [y - s for y, s in zip(y_vals, y_std)],
                               [y + s for y, s in zip(y_vals, y_std)],
                               alpha=0.2)
    
    ax.set_xlabel(x_label, fontsize=14)
    ax.set_ylabel(f"{metric_label}", fontsize=14)
    
    B_str = "_".join([str(B) for B in B_values]) if len(B_values) <= 5 else f"{len(B_values)}_B_values"
    title = f"{metric_label.capitalize()} vs {x_label} for B={B_str} (p=0.5, even split)"
    ax.set_title(title, fontsize=13)
    
    # Position legend to avoid covering data - use outside plot area if possible
    if len(B_values) <= 3:
        # Few lines: put legend outside
        ax.legend(fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), framealpha=0.9)
    else:
        # Many lines: use best location with transparency
        ax.legend(fontsize=9, loc='best', framealpha=0.9, ncol=2 if len(B_values) > 6 else 1)
    
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    # Save figure
    if save_dir is None:
        save_dir = "."
    os.makedirs(save_dir, exist_ok=True)
    
    metric_suffix = "timeavg" if metric == 'time_avg' else "final"
    x_suffix = "alpha" if x_axis == 'alpha' else "r"
    filename = f"even_split_B{B_str}_{x_suffix}_{metric_suffix}_fullness.png"
    filepath = os.path.join(save_dir, filename)
    fig.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"  Saved figure: {filepath}")
    
    plt.show()


def plot_all_B_separate(records, B_values=None, save_dir=None, metric='time_avg', show_range=True, x_axis='alpha'):
    """
    Plot separate figures for each B value.
    
    Parameters
    ----------
    records : list
        Data records
    B_values : list of int or None
        List of B values to plot (if None, plots all B values)
    save_dir : str or None
        Directory to save figures
    metric : str
        Which fullness metric: 'time_avg' (default) or 'final'
    show_range : bool
        If True, show min/max range as shaded area
    x_axis : str
        'alpha' (r/B) or 'r' (absolute r values)
    """
    import matplotlib.pyplot as plt
    
    if len(records) == 0:
        print("No records to plot!")
        return
    
    # Get unique B values
    all_B_values = sorted(list(dict.fromkeys([r['B'] for r in records])))
    
    if B_values is None:
        B_values = all_B_values
    else:
        B_values = [B for B in B_values if B in all_B_values]
        if not B_values:
            print(f"Error: None of the specified B values are in the data!")
            print(f"Available B values: {all_B_values}")
            return
    
    # Determine which fullness metric to use
    fullness_key = 'time_avg_fullness' if metric == 'time_avg' else 'fullness'
    fullness_min_key = fullness_key + '_min'
    fullness_max_key = fullness_key + '_max'
    fullness_std_key = fullness_key + '_std'
    metric_label = 'time-averaged fullness' if metric == 'time_avg' else 'final fullness'
    
    # Set save directory
    if save_dir is None:
        save_dir = "."
    os.makedirs(save_dir, exist_ok=True)
    
    # Plot each B separately
    for B in B_values:
        B_records = [r for r in records if r['B'] == B]
        B_records = sorted(B_records, key=lambda x: x['r'])
        
        if not B_records:
            continue
        
        # Extract data
        if x_axis == 'alpha':
            x_vals = [r['alpha'] for r in B_records]
            x_label = 'α = r / B'
        else:
            x_vals = [r['r'] for r in B_records]
            x_label = 'r (batch size)'
        
        y_vals = [r[fullness_key] for r in B_records]
        y_min = [r[fullness_min_key] for r in B_records]
        y_max = [r[fullness_max_key] for r in B_records]
        y_std = [r[fullness_std_key] for r in B_records]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot main curve
        ax.plot(x_vals, y_vals, marker='o', markersize=4, linewidth=2, 
                label=f'B={B}', alpha=0.8, color='blue')
        
        # Show range
        if show_range:
            if any(y_max[i] > y_min[i] for i in range(len(y_vals))):
                ax.fill_between(x_vals, y_min, y_max, alpha=0.2, color='blue')
            elif any(s > 0 for s in y_std):
                ax.fill_between(x_vals,
                               [y - s for y, s in zip(y_vals, y_std)],
                               [y + s for y, s in zip(y_vals, y_std)],
                               alpha=0.2, color='blue')
        
        ax.set_xlabel(x_label, fontsize=14)
        ax.set_ylabel(f"{metric_label}", fontsize=14)
        ax.set_title(f"{metric_label.capitalize()} vs {x_label} for B={B} (p=0.5, even split)", fontsize=13)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        
        # Save figure
        metric_suffix = "timeavg" if metric == 'time_avg' else "final"
        x_suffix = "alpha" if x_axis == 'alpha' else "r"
        filename = f"B{B}_{x_suffix}_{metric_suffix}_fullness.png"
        filepath = os.path.join(save_dir, filename)
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"  Saved figure: {filepath}")
        
        plt.close(fig)


def find_min_for_r_less_than_B_half(records, B_values=None, metric='time_avg'):
    """
    Find minimum fullness for r < B/2 for each B value.
    
    Parameters
    ----------
    records : list
        Data records
    B_values : list of int or None
        List of B values to analyze (if None, analyzes all B values)
    metric : str
        Which fullness metric: 'time_avg' (default) or 'final'
    
    Returns
    -------
    dict : {B: {'min_fullness': float, 'r_at_min': int, 'alpha_at_min': float}}
    """
    all_B_values = sorted(list(dict.fromkeys([r['B'] for r in records])))
    
    if B_values is None:
        B_values = all_B_values
    else:
        B_values = [B for B in B_values if B in all_B_values]
    
    fullness_key = 'time_avg_fullness' if metric == 'time_avg' else 'fullness'
    results = {}
    
    for B in B_values:
        B_records = [r for r in records if r['B'] == B and r['r'] < B / 2]
        if not B_records:
            continue
        
        # Find minimum
        min_record = min(B_records, key=lambda x: x[fullness_key])
        
        results[B] = {
            'min_fullness': min_record[fullness_key],
            'r_at_min': min_record['r'],
            'alpha_at_min': min_record['alpha'],
            'p': min_record['p']
        }
    
    return results


def plot_min_for_r_less_than_B_half(records, B_values=None, save_dir=None, metric='time_avg'):
    """
    Plot minimum fullness for r < B/2 vs B.
    
    Parameters
    ----------
    records : list
        Data records
    B_values : list of int or None
        List of B values to plot (if None, plots all B values)
    save_dir : str or None
        Directory to save figures
    metric : str
        Which fullness metric: 'time_avg' (default) or 'final'
    """
    import matplotlib.pyplot as plt
    
    min_results = find_min_for_r_less_than_B_half(records, B_values, metric)
    
    if not min_results:
        print("No data found for r < B/2!")
        return
    
    B_list = sorted(min_results.keys())
    min_fullness_vals = [min_results[B]['min_fullness'] for B in B_list]
    r_at_min_vals = [min_results[B]['r_at_min'] for B in B_list]
    alpha_at_min_vals = [min_results[B]['alpha_at_min'] for B in B_list]
    
    metric_label = 'time-averaged fullness' if metric == 'time_avg' else 'final fullness'
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Minimum fullness vs B
    ax1.plot(B_list, min_fullness_vals, marker='o', markersize=8, linewidth=2, color='blue')
    ax1.set_xlabel('B (block capacity)', fontsize=14)
    ax1.set_ylabel(f'Minimum {metric_label}', fontsize=14)
    ax1.set_title(f'Minimum {metric_label.capitalize()} for r < B/2', fontsize=13)
    ax1.grid(True, alpha=0.3)
    
    # Add value labels with smart positioning to avoid overlap
    y_range = max(min_fullness_vals) - min(min_fullness_vals)
    for i, (B, val) in enumerate(zip(B_list, min_fullness_vals)):
        # Alternate label position above/below to reduce overlap
        offset_y = 15 if i % 2 == 0 else -20
        # Use smaller font and adjust position based on data density
        ax1.annotate(f'{val:.4f}', (B, val), textcoords="offset points", 
                    xytext=(0, offset_y), ha='center', fontsize=8, 
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none'))
    
    # Plot 2: r at minimum vs B
    ax2.plot(B_list, r_at_min_vals, marker='s', markersize=8, linewidth=2, color='red', label='r at minimum')
    ax2_twin = ax2.twinx()
    ax2_twin.plot(B_list, alpha_at_min_vals, marker='^', markersize=8, linewidth=2, 
                  color='green', label='α at minimum')
    
    ax2.set_xlabel('B (block capacity)', fontsize=14)
    ax2.set_ylabel('r at minimum', fontsize=14, color='red')
    ax2_twin.set_ylabel('α = r/B at minimum', fontsize=14, color='green')
    ax2.set_title('r and α Values at Minimum Fullness (r < B/2)', fontsize=13)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='y', labelcolor='red')
    ax2_twin.tick_params(axis='y', labelcolor='green')
    
    # Add legends with better positioning to avoid covering data
    # Check data ranges to position legends intelligently
    r_range = max(r_at_min_vals) - min(r_at_min_vals) if r_at_min_vals else 0
    alpha_range = max(alpha_at_min_vals) - min(alpha_at_min_vals) if alpha_at_min_vals else 0
    
    # Position legends in areas with less data
    if len(B_list) > 0:
        # Put legends at opposite ends
        ax2.legend(loc='upper left', framealpha=0.9)
        ax2_twin.legend(loc='lower right', framealpha=0.9)
    else:
        ax2.legend(loc='best', framealpha=0.9)
        ax2_twin.legend(loc='best', framealpha=0.9)
    
    fig.tight_layout()
    
    # Save figure
    if save_dir is None:
        save_dir = "."
    os.makedirs(save_dir, exist_ok=True)
    
    metric_suffix = "timeavg" if metric == 'time_avg' else "final"
    filename = f"even_split_min_r_less_B_half_{metric_suffix}.png"
    filepath = os.path.join(save_dir, filename)
    fig.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"  Saved figure: {filepath}")
    
    plt.show()


def print_summary(records, B_values=None):
    """Print summary statistics for each B value."""
    
    all_B_values = sorted(list(dict.fromkeys([r['B'] for r in records])))
    
    if B_values is None:
        B_values = all_B_values
    else:
        B_values = [B for B in B_values if B in all_B_values]
    
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    for B in B_values:
        B_records = [r for r in records if r['B'] == B]
        if not B_records:
            continue
        
        # Get ranges
        r_min = min(r['r'] for r in B_records)
        r_max = max(r['r'] for r in B_records)
        alpha_min = min(r['alpha'] for r in B_records)
        alpha_max = max(r['alpha'] for r in B_records)
        
        # Get fullness ranges
        fullness_vals = [r['time_avg_fullness'] for r in B_records]
        fullness_min_val = min(fullness_vals)
        fullness_max_val = max(fullness_vals)
        fullness_mean = sum(fullness_vals) / len(fullness_vals)
        
        # Get minimum for r < B/2
        r_less_than_half = [r for r in B_records if r['r'] < B / 2]
        if r_less_than_half:
            min_r_less_half = min(r_less_than_half, key=lambda x: x['time_avg_fullness'])
            min_r_less_half_val = min_r_less_half['time_avg_fullness']
            min_r_less_half_r = min_r_less_half['r']
            min_r_less_half_alpha = min_r_less_half['alpha']
        else:
            min_r_less_half_val = None
            min_r_less_half_r = None
            min_r_less_half_alpha = None
        
        print(f"\nB = {B}:")
        print(f"  r range: {r_min} to {r_max} ({r_max - r_min + 1} values)")
        print(f"  α range: {alpha_min:.4f} to {alpha_max:.4f}")
        print(f"  Time-avg fullness range: {fullness_min_val:.4f} to {fullness_max_val:.4f}")
        print(f"  Time-avg fullness mean: {fullness_mean:.4f}")
        if min_r_less_half_val is not None:
            print(f"  Min fullness for r < B/2: {min_r_less_half_val:.4f} at r={min_r_less_half_r}, α={min_r_less_half_alpha:.4f}")
        print(f"  Records: {len(B_records)}")


def main():
    """Main analysis pipeline."""
    parser = argparse.ArgumentParser(
        description='Analyze even split (p=0.5) simulation results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plot all B values together
  python analyze_even_split_results.py --input aggregated_results.csv
  
  # Plot specific B values
  python analyze_even_split_results.py --input aggregated_results.csv --B 256 320 384
  
  # Plot B values in a range
  python analyze_even_split_results.py --input aggregated_results.csv --B-min 256 --B-max 320
  
  # Plot each B separately
  python analyze_even_split_results.py --input aggregated_results.csv --separate
  
  # Use r instead of alpha on x-axis
  python analyze_even_split_results.py --input aggregated_results.csv --x-axis r
  
  # Hide range shading
  python analyze_even_split_results.py --input aggregated_results.csv --no-range
  
  # Plot minimum fullness for r < B/2
  python analyze_even_split_results.py --input aggregated_results.csv --min-r-less-half
        """
    )
    parser.add_argument('--input', '-i', default='aggregated_results.csv', 
                       help='Input CSV file (default: aggregated_results.csv)')
    parser.add_argument('--B', type=int, nargs='+', default=None,
                       help='Specify which B values to plot (default: all B values)')
    parser.add_argument('--B-min', type=int, default=None,
                       help='Minimum B value (use with --B-max to specify range)')
    parser.add_argument('--B-max', type=int, default=None,
                       help='Maximum B value (use with --B-min to specify range)')
    parser.add_argument('--save-dir', '-s', default=None,
                       help='Directory to save figures (default: same directory as input CSV)')
    parser.add_argument('--separate', action='store_true',
                       help='Create separate figure for each B value')
    parser.add_argument('--x-axis', choices=['alpha', 'r'], default='alpha',
                       help='X-axis: alpha (r/B) or r (default: alpha)')
    parser.add_argument('--no-range', action='store_true',
                       help='Hide min/max range shading')
    parser.add_argument('--metric', '-m', default='time_avg', choices=['time_avg', 'final'],
                       help='Fullness metric: time_avg (default) or final')
    parser.add_argument('--min-r-less-half', action='store_true',
                       help='Plot minimum fullness for r < B/2 vs B')
    
    args = parser.parse_args()
    
    print("="*80)
    print("EVEN SPLIT SIMULATION - RESULTS ANALYSIS")
    print("="*80)
    
    # Load data
    print(f"\nLoading data from: {args.input}")
    records = load_results_from_csv(args.input)
    
    if len(records) == 0:
        print("No data to analyze!")
        return
    
    # Get unique B values
    all_B_values = sorted(list(dict.fromkeys([r['B'] for r in records])))
    print(f"\nFound B values: {len(all_B_values)} values from {min(all_B_values)} to {max(all_B_values)}")
    
    # Determine which B values to use
    B_values_to_use = None
    if args.B is not None:
        # Use explicitly specified B values
        B_values_to_use = args.B
        print(f"Using specified B values: {B_values_to_use}")
    elif args.B_min is not None or args.B_max is not None:
        # Use B range
        B_min = args.B_min if args.B_min is not None else min(all_B_values)
        B_max = args.B_max if args.B_max is not None else max(all_B_values)
        B_values_to_use = [B for B in all_B_values if B_min <= B <= B_max]
        print(f"Using B range: {B_min} to {B_max} ({len(B_values_to_use)} values)")
    else:
        # Use all B values
        B_values_to_use = None
        print(f"Using all B values: {len(all_B_values)} values")
    
    # Determine save directory
    if args.save_dir is None:
        save_dir = os.path.dirname(args.input) if os.path.dirname(args.input) else "."
    else:
        save_dir = args.save_dir
    print(f"Figures will be saved to: {save_dir}")
    
    # Print summary
    print_summary(records, B_values=B_values_to_use)
    
    # Plot minimum for r < B/2 if requested
    if args.min_r_less_half:
        print(f"\nAnalyzing minimum fullness for r < B/2...")
        min_results = find_min_for_r_less_than_B_half(records, B_values=B_values_to_use, metric=args.metric)
        
        if min_results:
            print("\nMinimum fullness for r < B/2:")
            print(f"{'B':<8} {'Min Fullness':<15} {'r at min':<12} {'α at min':<12}")
            print("-" * 50)
            for B in sorted(min_results.keys()):
                res = min_results[B]
                print(f"{B:<8} {res['min_fullness']:<15.6f} {res['r_at_min']:<12} {res['alpha_at_min']:<12.6f}")
            
            plot_min_for_r_less_than_B_half(records, B_values=B_values_to_use, save_dir=save_dir, metric=args.metric)
        else:
            print("No data found for r < B/2!")
    
    # Plot main curves
    show_range = not args.no_range
    
    if args.separate:
        print(f"\nCreating separate figures for each B value...")
        plot_all_B_separate(records, B_values=B_values_to_use, save_dir=save_dir, 
                           metric=args.metric, show_range=show_range, x_axis=args.x_axis)
    else:
        print(f"\nCreating combined figure for all B values...")
        plot_by_B(records, B_values=B_values_to_use, save_dir=save_dir, 
                 metric=args.metric, show_range=show_range, x_axis=args.x_axis)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()

