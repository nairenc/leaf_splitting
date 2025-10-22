"""
analyze_results.py
Load and visualize sweep_results.csv from deferred split simulations.
Uses the same plotting logic as deferred_split_sim_sweep.py
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
            return records
        
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

def plot_results(records, B=None, save_dir=None, metric='time_avg'):
    """
    Create 2 figures analyzing the sweep results.
    Figure 1: Maximum fullness (over p) vs r/B with optimal p values
    Figure 2: Minimum fullness (over r) vs p with worst r values
    
    Parameters
    ----------
    records : list
        Data records
    B : int or None
        Block size to filter by
    save_dir : str or None
        Directory to save figures (if None, uses current directory)
    metric : str
        Which fullness metric to plot: 'time_avg' (default) or 'final'
    """
    try:
        import matplotlib.pyplot as plt
        import os
        
        if len(records) == 0:
            print("No records to plot!")
            return
        
        # Set save directory
        if save_dir is None:
            save_dir = "."
        os.makedirs(save_dir, exist_ok=True)
        
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
        r_unique = sorted(list(dict.fromkeys([row["r"] for row in records])))
        
        print(f"Seeds: {len(seeds_unique)}, p values: {len(p_unique)}, r values: {len(r_unique)}")
        
        # Figure 1: x=r (or alpha), y=max_p fullness (averaged over seeds)
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        r_vals = []
        alpha_vals = []
        max_fullness_vals = []
        best_p_vals = []
        
        for r_val in r_unique:
            # For each r, find the max fullness over all p (averaged over seeds)
            best_fullness = -1
            best_p = None
            for p_val in p_unique:
                fullnesses = [row[fullness_key] for row in records 
                             if row["r"] == r_val and row["p"] == p_val]
                if fullnesses:
                    avg_fullness = sum(fullnesses) / len(fullnesses)
                    if avg_fullness > best_fullness:
                        best_fullness = avg_fullness
                        best_p = p_val
            
            if best_fullness > -1:
                r_vals.append(r_val)
                alpha_vals.append(r_val / B)
                max_fullness_vals.append(best_fullness)
                best_p_vals.append(best_p)
        
        ax1.plot(alpha_vals, max_fullness_vals, marker='o', linewidth=2, label=f"max_p {metric_label}")
        ax1.set_xlabel("alpha = r / B")
        ax1.set_ylabel(f"max_p {metric_label}")
        ax1.set_title(f"Maximum {metric_label} (over p) vs r/B (B={B}, {len(seeds_unique)} seeds)")
        
        # Add a secondary axis showing the optimal p values
        ax1_twin = ax1.twinx()
        ax1_twin.plot(alpha_vals, best_p_vals, marker='x', linestyle='--', 
                     color='orange', alpha=0.7, label="optimal p")
        ax1_twin.set_ylabel("optimal p", color='orange')
        ax1_twin.tick_params(axis='y', labelcolor='orange')
        
        # Combine legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax1_twin.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')
        
        ax1.grid(True, alpha=0.3)
        fig1.tight_layout()
        
        # Save Figure 1
        r_min, r_max = min(r_unique), max(r_unique)
        p_min, p_max = min(p_unique), max(p_unique)
        metric_suffix = 'timeavg' if metric == 'time_avg' else 'final'
        fig1_filename = f"B{B}_r{r_min}-{r_max}_p{p_min:.2f}-{p_max:.2f}_maxp_{metric_suffix}_fullness_vs_alpha.png"
        fig1_path = os.path.join(save_dir, fig1_filename)
        fig1.savefig(fig1_path, dpi=300, bbox_inches='tight')
        print(f"  Saved Figure 1: {fig1_path}")
        
        # Figure 2: x=p, y=min_r fullness (minimum fullness over all r values for each p)
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        p_vals = []
        min_fullness_vals = []
        worst_r_vals = []
        
        for p_val in p_unique:
            # For each p, find the min fullness over all r (averaged over seeds)
            worst_fullness = float('inf')
            worst_r = None
            for r_val in r_unique:
                fullnesses = [row[fullness_key] for row in records 
                             if row["r"] == r_val and row["p"] == p_val]
                if fullnesses:
                    avg_fullness = sum(fullnesses) / len(fullnesses)
                    if avg_fullness < worst_fullness:
                        worst_fullness = avg_fullness
                        worst_r = r_val
            
            if worst_fullness < float('inf'):
                p_vals.append(p_val)
                min_fullness_vals.append(worst_fullness)
                worst_r_vals.append(worst_r)
        
        ax2.plot(p_vals, min_fullness_vals, marker='o', linewidth=2, color='red')
        ax2.set_xlabel("p (split ratio)")
        ax2.set_ylabel(f"min_r {metric_label}")
        ax2.set_title(f"Minimum {metric_label} (over r) vs p (B={B}, {len(seeds_unique)} seeds)")
        
        # Add a secondary axis showing which r value was worst
        ax2_twin = ax2.twinx()
        ax2_twin.plot(p_vals, worst_r_vals, marker='x', linestyle='--', 
                     color='purple', alpha=0.7, label="worst r")
        ax2_twin.set_ylabel("worst r (minimum fullness)", color='purple')
        ax2_twin.tick_params(axis='y', labelcolor='purple')
        
        # Combine legends
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='best')
        
        ax2.grid(True, alpha=0.3)
        fig2.tight_layout()
        
        # Save Figure 2
        fig2_filename = f"B{B}_r{r_min}-{r_max}_p{p_min:.2f}-{p_max:.2f}_minr_{metric_suffix}_fullness_vs_p.png"
        fig2_path = os.path.join(save_dir, fig2_filename)
        fig2.savefig(fig2_path, dpi=300, bbox_inches='tight')
        print(f"  Saved Figure 2: {fig2_path}")
        
        plt.show()
        
    except Exception as e:
        print(f"Plotting failed: {e}")
        raise

def main():
    """Main analysis pipeline."""
    parser = argparse.ArgumentParser(description='Analyze deferred split simulation results')
    parser.add_argument('--input', '-i', default='sweep_results.csv', 
                       help='Input CSV file (default: sweep_results.csv)')
    parser.add_argument('--B', type=int, default=None,
                       help='Specify which B value to plot (default: first B value in data)')
    parser.add_argument('--save-dir', '-s', default=None,
                       help='Directory to save figures (default: same directory as input CSV)')
    parser.add_argument('--metric', '-m', default='time_avg', choices=['time_avg', 'final'],
                       help='Fullness metric to plot: time_avg (default, more stable) or final (snapshot)')
    
    args = parser.parse_args()
    
    print("="*80)
    print("DEFERRED SPLIT SIMULATION - RESULTS ANALYSIS")
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
    
    plot_results(records, B=plot_B, save_dir=save_dir, metric=args.metric)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)

if __name__ == "__main__":
    main()
