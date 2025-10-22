"""
analyze_results_filtered.py
Load and visualize sweep_results.csv with filtering options.
Can filter by specific r value (showing lines for different p) 
or specific p value (showing lines for different r).
"""

import csv
import argparse

def load_results_from_csv(filename='sweep_results.csv'):
    """Load the CSV data and return as list of dictionaries.
    
    Works with both deferred_split and immediately_split CSVs.
    Automatically detects aggregated vs per-seed format.
    
    Per-seed format requires: B, r, alpha, p, seed, fullness
    Aggregated format requires: B, r, alpha, p, fullness_mean, n_seeds
    """
    records = []
    is_aggregated = False
    
    with open(filename, 'r', newline='') as f:
        reader = csv.DictReader(f)
        
        # Peek at first row to detect format
        first_row = next(reader, None)
        if first_row is None:
            print(f"Warning: {filename} is empty")
            return records, is_aggregated
        
        # Detect if this is aggregated data
        if 'fullness_mean' in first_row:
            is_aggregated = True
            print(f"Detected aggregated data format (fullness_mean column found)")
        elif 'seed' in first_row:
            is_aggregated = False
            print(f"Detected per-seed data format (seed column found)")
        else:
            print(f"Warning: Could not detect data format, assuming per-seed")
            is_aggregated = False
        
        # Reset to beginning
        f.seek(0)
        reader = csv.DictReader(f)
        
        for row in reader:
            # Convert base fields
            record = {
                'B': int(row['B']),
                'r': int(row['r']),
                'alpha': float(row['alpha']),
                'p': float(row['p']),
            }
            
            if is_aggregated:
                # Aggregated format
                record['fullness'] = float(row['fullness_mean'])
                record['fullness_std'] = float(row.get('fullness_std', 0))
                record['n_seeds'] = int(row['n_seeds'])
                record['is_aggregated'] = True
                
                # Load time_avg_fullness if present
                if 'time_avg_fullness_mean' in row:
                    record['time_avg_fullness'] = float(row['time_avg_fullness_mean'])
                    record['time_avg_fullness_std'] = float(row.get('time_avg_fullness_std', 0))
                else:
                    record['time_avg_fullness'] = record['fullness']
                    record['time_avg_fullness_std'] = record['fullness_std']
                
                # Use a placeholder seed of 0 for aggregated data
                record['seed'] = 0
            else:
                # Per-seed format
                record['seed'] = int(row['seed'])
                record['fullness'] = float(row['fullness'])
                record['is_aggregated'] = False
                
                # Load time_avg_fullness if present
                if 'time_avg_fullness' in row:
                    record['time_avg_fullness'] = float(row['time_avg_fullness'])
                else:
                    record['time_avg_fullness'] = float(row['fullness'])
            
            # Optional fields (for backwards compatibility)
            for optional_field in ['mu', 'p_H_emp', 'k_H', 'k_L', 's', 'T', 
                                   'p_min', 'p_max', 'final_fullness', 'final_blocks']:
                if optional_field in row:
                    if optional_field in ['s', 'T', 'final_blocks']:
                        record[optional_field] = int(row[optional_field])
                    else:
                        record[optional_field] = float(row[optional_field])
            
            records.append(record)
    
    print(f"Loaded {len(records)} records from {filename}")
    return records, is_aggregated


def plot_fixed_r(records, r_values, B=None, use_ratios=True, save_dir=None, metric='time_avg'):
    """
    Plot fullness vs p for specific r value(s).
    
    Parameters
    ----------
    records : list
        Data records
    r_values : list of float or int
        List of r/B ratios (if use_ratios=True) or exact r values (if use_ratios=False)
    B : int or None
        Block size to filter by
    use_ratios : bool
        If True, r_values are r/B ratios; if False, r_values are exact integers
    save_dir : str or None
        Directory to save figures (if None, uses current directory)
    metric : str
        Which fullness metric to plot: 'time_avg' (default) or 'final'
    """
    import matplotlib.pyplot as plt
    import os
    
    if len(records) == 0:
        print("No records to plot!")
        return
    
    # If B not specified, use the first B value in the data
    if B is None:
        B = records[0]['B']
    
    # Filter records for the specified B value
    records = [r for r in records if r['B'] == B]
    print(f"Plotting {len(records)} records for B={B}")
    
    # Determine which fullness metric to use
    fullness_key = 'time_avg_fullness' if metric == 'time_avg' else 'fullness'
    metric_label = 'time-averaged fullness' if metric == 'time_avg' else 'final fullness'
    print(f"Using metric: {metric_label} (column: {fullness_key})")
    
    # Extract unique values
    seeds_unique = list(dict.fromkeys([row["seed"] for row in records]))
    p_unique = sorted(list(dict.fromkeys([row["p"] for row in records])))
    r_available = sorted(list(dict.fromkeys([row["r"] for row in records])))
    
    print(f"Seeds: {len(seeds_unique)}, p values: {len(p_unique)}, r values available: {len(r_available)}")
    
    # Convert to actual r values
    if use_ratios:
        # Convert r_ratios to actual r values by finding closest match
        def find_closest_r(target_ratio, B, available_r_list):
            """Find the closest r value in the data for a given r/B ratio."""
            target_r = target_ratio * B
            return min(available_r_list, key=lambda x: abs(x - target_r))
        
        valid_r_values = []
        for ratio in r_values:
            r_closest = find_closest_r(ratio, B, r_available)
            alpha_closest = r_closest / B
            if r_closest not in valid_r_values:
                valid_r_values.append(r_closest)
                print(f"  r/B = {ratio:.4f} → r = {r_closest} (actual r/B = {alpha_closest:.4f})")
    else:
        # Use exact r values
        valid_r_values = []
        for r_val in r_values:
            r_int = int(r_val)
            if r_int in r_available:
                if r_int not in valid_r_values:
                    valid_r_values.append(r_int)
                    alpha = r_int / B
                    print(f"  r = {r_int} (r/B = {alpha:.4f})")
            else:
                print(f"  Warning: r = {r_int} not found in data")
    
    if len(valid_r_values) == 0:
        print(f"Error: Could not find any valid r values!")
        return
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Check if data is aggregated
    is_aggregated = records[0].get('is_aggregated', False) if records else False
    std_key = fullness_key + '_std' if is_aggregated else None
    
    for r_val in valid_r_values:
        # For each p, average fullness over all seeds
        p_vals = []
        fullness_vals = []
        fullness_std = []
        
        for p_val in p_unique:
            matching_rows = [row for row in records 
                            if row["r"] == r_val and row["p"] == p_val]
            
            if matching_rows:
                p_vals.append(p_val)
                
                if is_aggregated:
                    # Use pre-computed statistics
                    fullness_vals.append(matching_rows[0][fullness_key])
                    if std_key and std_key in matching_rows[0]:
                        fullness_std.append(matching_rows[0][std_key])
                    else:
                        fullness_std.append(0)
                else:
                    # Compute average over seeds
                    fullnesses = [row[fullness_key] for row in matching_rows]
                    avg = sum(fullnesses) / len(fullnesses)
                    fullness_vals.append(avg)
                    
                    # Calculate standard deviation if multiple seeds
                    if len(fullnesses) > 1:
                        import math
                        variance = sum((x - avg)**2 for x in fullnesses) / len(fullnesses)
                        std = math.sqrt(variance)
                        fullness_std.append(std)
                    else:
                        fullness_std.append(0)
        
        if p_vals:
            alpha = r_val / B
            ax.plot(p_vals, fullness_vals, marker='o', label=f"r={r_val} (α={alpha:.3f})")
            
            # Optionally add error bars if we have multiple seeds
            if len(seeds_unique) > 1 and any(s > 0 for s in fullness_std):
                ax.fill_between(p_vals, 
                               [f - s for f, s in zip(fullness_vals, fullness_std)],
                               [f + s for f, s in zip(fullness_vals, fullness_std)],
                               alpha=0.2)
    
    ax.set_xlabel("p (split ratio)", fontsize=12)
    ax.set_ylabel(f"{metric_label}", fontsize=12)
    ax.set_title(f"{metric_label.capitalize()} vs p for r={valid_r_values} (B={B}, {len(seeds_unique)} seeds)", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    # Save figure
    if save_dir is None:
        save_dir = "."
    os.makedirs(save_dir, exist_ok=True)
    
    p_min, p_max = min(p_unique), max(p_unique)
    r_str = "_".join([str(r) for r in valid_r_values])
    filename = f"B{B}_r{r_str}_p{p_min:.2f}-{p_max:.2f}_fullness_vs_p.png"
    filepath = os.path.join(save_dir, filename)
    fig.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"  Saved figure: {filepath}")
    
    plt.show()


def plot_fixed_p(records, p_values, B=None, save_dir=None, metric='time_avg'):
    """
    Plot fullness vs r (or alpha) for specific p value(s).
    
    Parameters
    ----------
    records : list
        Data records
    p_values : list of float
        List of p values to plot
    B : int or None
        Block size to filter by
    save_dir : str or None
        Directory to save figures (if None, uses current directory)
    metric : str
        Which fullness metric to plot: 'time_avg' (default) or 'final'
    """
    import matplotlib.pyplot as plt
    import os
    
    if len(records) == 0:
        print("No records to plot!")
        return
    
    # If B not specified, use the first B value in the data
    if B is None:
        B = records[0]['B']
    
    # Filter records for the specified B value
    records = [r for r in records if r['B'] == B]
    print(f"Plotting {len(records)} records for B={B}")
    
    # Determine which fullness metric to use
    fullness_key = 'time_avg_fullness' if metric == 'time_avg' else 'fullness'
    metric_label = 'time-averaged fullness' if metric == 'time_avg' else 'final fullness'
    print(f"Using metric: {metric_label} (column: {fullness_key})")
    
    # Extract unique values
    seeds_unique = list(dict.fromkeys([row["seed"] for row in records]))
    r_unique = sorted(list(dict.fromkeys([row["r"] for row in records])))
    p_available = sorted(list(dict.fromkeys([row["p"] for row in records])))
    
    print(f"Seeds: {len(seeds_unique)}, r values: {len(r_unique)}, p values available: {len(p_available)}")
    
    # Find closest p values in data (since p might not match exactly)
    def find_closest_p(target_p, available_p_list):
        """Find the closest p value in the data."""
        return min(available_p_list, key=lambda x: abs(x - target_p))
    
    valid_p_values = []
    for p_target in p_values:
        p_closest = find_closest_p(p_target, p_available)
        if abs(p_closest - p_target) < 0.01:  # Within 1% tolerance
            if p_closest not in valid_p_values:
                valid_p_values.append(p_closest)
        else:
            print(f"Warning: p={p_target} not found (closest: {p_closest})")
    
    if len(valid_p_values) == 0:
        print(f"Error: None of the specified p values {p_values} are in the data!")
        print(f"Available p values: {p_available}")
        return
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Check if data is aggregated
    is_aggregated = records[0].get('is_aggregated', False) if records else False
    std_key = fullness_key + '_std' if is_aggregated else None
    
    for p_val in valid_p_values:
        # For each r, average fullness over all seeds
        r_vals = []
        alpha_vals = []
        fullness_vals = []
        fullness_std = []
        
        for r_val in r_unique:
            matching_rows = [row for row in records 
                            if row["r"] == r_val and abs(row["p"] - p_val) < 0.001]
            
            if matching_rows:
                r_vals.append(r_val)
                alpha_vals.append(r_val / B)
                
                if is_aggregated:
                    # Use pre-computed statistics
                    fullness_vals.append(matching_rows[0][fullness_key])
                    if std_key and std_key in matching_rows[0]:
                        fullness_std.append(matching_rows[0][std_key])
                    else:
                        fullness_std.append(0)
                else:
                    # Compute average over seeds
                    fullnesses = [row[fullness_key] for row in matching_rows]
                    avg = sum(fullnesses) / len(fullnesses)
                    fullness_vals.append(avg)
                    
                    # Calculate standard deviation if multiple seeds
                    if len(fullnesses) > 1:
                        import math
                        variance = sum((x - avg)**2 for x in fullnesses) / len(fullnesses)
                        std = math.sqrt(variance)
                        fullness_std.append(std)
                    else:
                        fullness_std.append(0)
        
        if r_vals:
            ax.plot(alpha_vals, fullness_vals, marker='o', label=f"p={p_val:.3f}")
            
            # Optionally add error bars if we have multiple seeds
            if len(seeds_unique) > 1 and any(s > 0 for s in fullness_std):
                ax.fill_between(alpha_vals,
                               [f - s for f, s in zip(fullness_vals, fullness_std)],
                               [f + s for f, s in zip(fullness_vals, fullness_std)],
                               alpha=0.2)
    
    ax.set_xlabel("alpha = r / B", fontsize=12)
    ax.set_ylabel(f"{metric_label}", fontsize=12)
    ax.set_title(f"{metric_label.capitalize()} vs α for p={valid_p_values} (B={B}, {len(seeds_unique)} seeds)", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    # Save figure
    if save_dir is None:
        save_dir = "."
    os.makedirs(save_dir, exist_ok=True)
    
    r_min, r_max = min(r_unique), max(r_unique)
    p_str = "_".join([f"{p:.2f}" for p in valid_p_values])
    filename = f"B{B}_r{r_min}-{r_max}_p{p_str}_fullness_vs_alpha.png"
    filepath = os.path.join(save_dir, filename)
    fig.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"  Saved figure: {filepath}")
    
    plt.show()


def main():
    """Main analysis pipeline."""
    parser = argparse.ArgumentParser(
        description='Analyze deferred split simulation results with filtering',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plot fullness vs p for specific r/B ratios (alpha values)
  python analyze_results_filtered.py --input results.csv --r 0.04 0.08 0.16 0.25
  
  # Plot fullness vs p for exact integer r values
  python analyze_results_filtered.py --input results.csv --R 10 20 50 100
  
  # Plot fullness vs r for specific p values
  python analyze_results_filtered.py --input results.csv --p 0.3 0.4 0.5
  
  # Plot fullness vs r for exact p values (same as --p)
  python analyze_results_filtered.py --input results.csv --P 0.3 0.4 0.5
  
  # Specify B value
  python analyze_results_filtered.py --input results.csv --B 256 --r 0.1 0.2
  
  # For B=256: r/B=0.04 corresponds to r≈10, r/B=0.25 corresponds to r=64
        """
    )
    parser.add_argument('--input', '-i', default='sweep_results.csv', 
                       help='Input CSV file (default: sweep_results.csv)')
    parser.add_argument('--B', type=int, default=None,
                       help='Specify which B value to plot (default: first B value in data)')
    parser.add_argument('--save-dir', '-s', default=None,
                       help='Directory to save figures (default: same directory as input CSV)')
    
    # Mutually exclusive group: either filter by r or by p
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--r', type=float, nargs='+', metavar='RATIO',
                       help='Plot for specific r/B ratio(s), i.e., alpha values (shows lines for different p)')
    group.add_argument('--R', type=int, nargs='+', metavar='INT',
                       help='Plot for exact integer r value(s) (shows lines for different p)')
    group.add_argument('--p', type=float, nargs='+', metavar='P',
                       help='Plot for specific p value(s) (shows lines for different r)')
    group.add_argument('--P', type=float, nargs='+', metavar='P',
                       help='Plot for exact p value(s) (alias for --p, shows lines for different r)')
    
    parser.add_argument('--metric', '-m', default='time_avg', choices=['time_avg', 'final'],
                       help='Fullness metric to plot: time_avg (default, more stable) or final (snapshot)')
    
    args = parser.parse_args()
    
    print("="*80)
    print("DEFERRED SPLIT SIMULATION - FILTERED RESULTS ANALYSIS")
    print("="*80)
    
    # Load data
    print(f"Loading data from: {args.input}")
    records, is_aggregated = load_results_from_csv(args.input)
    
    if len(records) == 0:
        print("No data to analyze!")
        return
    
    if is_aggregated:
        print("Note: Using aggregated data (statistics already computed across seeds)")
    
    # Determine save directory
    if args.save_dir is None:
        import os
        # Default: save in the same directory as the input file
        save_dir = os.path.dirname(args.input) if os.path.dirname(args.input) else "."
    else:
        save_dir = args.save_dir
    print(f"Figures will be saved to: {save_dir}")
    
    # Get unique B values
    B_values = sorted(list(dict.fromkeys([r['B'] for r in records])))
    print(f"\nFound B values: {B_values}")
    
    # Determine which B value to plot
    if args.B is not None:
        if args.B in B_values:
            plot_B = args.B
            print(f"\nPlotting results for B={plot_B} (specified by user)")
        else:
            print(f"\nWarning: B={args.B} not found in data. Available: {B_values}")
            print(f"Using B={B_values[0]} instead")
            plot_B = B_values[0]
    else:
        plot_B = B_values[0]
        if len(B_values) > 1:
            print(f"\nPlotting results for B={plot_B} (first B value)")
            print(f"(Use --B to specify a different B value)")
        else:
            print(f"\nPlotting results for B={plot_B}")
    
    # Plot based on filtering option
    if args.r is not None:
        print(f"\nFiltering by r/B ratios (alpha): {args.r}")
        print("Plotting: fullness vs p")
        plot_fixed_r(records, args.r, B=plot_B, use_ratios=True, save_dir=save_dir, metric=args.metric)
    elif args.R is not None:
        print(f"\nFiltering by exact r values: {args.R}")
        print("Plotting: fullness vs p")
        plot_fixed_r(records, args.R, B=plot_B, use_ratios=False, save_dir=save_dir, metric=args.metric)
    elif args.p is not None:
        print(f"\nFiltering by p values: {args.p}")
        print("Plotting: fullness vs r (alpha)")
        plot_fixed_p(records, args.p, B=plot_B, save_dir=save_dir, metric=args.metric)
    elif args.P is not None:
        print(f"\nFiltering by exact p values: {args.P}")
        print("Plotting: fullness vs r (alpha)")
        plot_fixed_p(records, args.P, B=plot_B, save_dir=save_dir, metric=args.metric)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()

