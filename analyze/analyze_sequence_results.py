#!/usr/bin/env python3
"""
Analyze and visualize sequence simulation results.

Expects aggregated CSV from collect command with one row per repetition point.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import sys


def analyze_and_plot(csv_file):
    """
    Analyze convergence and generate plots from aggregated results.
    
    Plots are automatically saved in the same directory as the input CSV
    with prefix "analysis".
    
    Parameters
    ----------
    csv_file : str
        Path to aggregated CSV file (one row per repetition)
    """
    import os
    
    # Load data
    df = pd.read_csv(csv_file)
    df_sorted = df.sort_values('repetition')
    
    # Determine output prefix (same folder as input, name "analysis")
    input_dir = os.path.dirname(csv_file)
    if input_dir:
        output_prefix = os.path.join(input_dir, 'analysis')
    else:
        output_prefix = 'analysis'
    
    # Extract configuration from first row
    first_row = df.iloc[0]
    B = int(first_row['B'])
    method = first_row['method']
    p = float(first_row['p'])
    mean_alpha = float(first_row['mean_alpha'])
    n_seeds = int(first_row['n_seeds']) if 'n_seeds' in first_row else "unknown"
    
    print(f"Loaded {len(df)} time points")
    print(f"  Aggregated across {n_seeds} seeds")
    print(f"\nConfiguration:")
    print(f"  B = {B}")
    print(f"  Method = {method}")
    print(f"  p = {p:.3f}")
    print(f"  Mean alpha = {mean_alpha:.3f}")
    
    # Get final results
    final_row = df_sorted.iloc[-1]
    final_rep = int(final_row['repetition'])
    final_time_avg = float(final_row['time_avg_fullness_mean'])
    final_std = float(final_row['time_avg_fullness_std'])
    final_fullness = float(final_row['fullness_mean'])
    final_fullness_std = float(final_row['fullness_std'])
    
    print(f"\nFinal Results (at repetition {final_rep:,}):")
    print(f"  Time-avg fullness: {final_time_avg:.6f} +/- {final_std:.6f}")
    print(f"  Snapshot fullness: {final_fullness:.6f} +/- {final_fullness_std:.6f}")
    
    # Check convergence
    if len(df_sorted) >= 2:
        penultimate = df_sorted.iloc[-2]
        change = abs(final_row['time_avg_fullness_mean'] - penultimate['time_avg_fullness_mean'])
        print(f"  Change in last interval: {change:.8f}")
        if change < 0.0001:
            print(f"  Status: CONVERGED (change < 0.0001)")
        elif change < 0.001:
            print(f"  Status: Near convergence (change < 0.001)")
    else:
            print(f"  Status: May need more repetitions")
    
    # Compare to theoretical bounds
    if abs(p - 0.5) < 0.01:
        ln2 = np.log(2)
        diff = final_time_avg - ln2
        print(f"\nComparison to theory:")
        print(f"  ln(2) = {ln2:.6f} (expected for r=1, p=0.5)")
        print(f"  Difference: {diff:+.6f} ({diff/ln2*100:+.2f}%)")
    elif abs(p - 0.6) < 0.01:
        bound_5_9 = 5/9
        margin = final_time_avg - bound_5_9
        print(f"\nComparison to theory:")
        print(f"  5/9 = {bound_5_9:.6f} (theoretical lower bound for p=0.6)")
        print(f"  Margin above bound: {margin:+.6f} ({margin/bound_5_9*100:+.2f}%)")
        if margin < 0:
            print(f"  WARNING: Result is BELOW theoretical bound!")
        elif margin < 0.02:
            print(f"  CAUTION: Result is close to bound (near-adversarial)")
        else:
            print(f"  OK: Result is safely above bound")
    
    # Generate plots
    print(f"\nGenerating plots...")
    generate_plots(df_sorted, B, method, p, mean_alpha, output_prefix)
    print(f"  Saved: {output_prefix}_convergence.png")
    print(f"  Saved: {output_prefix}_convergence_detail.png")
    
    return {
        'final_time_avg_fullness': final_time_avg,
        'final_std': final_std,
        'final_repetition': final_rep,
        'B': B,
        'method': method,
        'p': p,
        'mean_alpha': mean_alpha,
    }


def generate_plots(df, B, method, p, mean_alpha, output_prefix):
    """Generate convergence analysis plots."""
    
    # Plot 1: Full convergence (2 panels)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Left panel: Time-averaged fullness
    axes[0].plot(df['repetition'], df['time_avg_fullness_mean'], 
                linewidth=2, color='red', label='Mean')
    axes[0].fill_between(df['repetition'], 
                        df['time_avg_fullness_mean'] - df['time_avg_fullness_std'],
                        df['time_avg_fullness_mean'] + df['time_avg_fullness_std'],
                        alpha=0.2, color='red', label='±1 std')
    
    axes[0].set_xlabel('Repetition (sequence cycles)', fontsize=12)
    axes[0].set_ylabel('Time-Averaged Fullness', fontsize=12)
    axes[0].set_title('Convergence: Time-Averaged Fullness', fontsize=13, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=10)
    
    # Right panel: Snapshot fullness
    axes[1].plot(df['repetition'], df['fullness_mean'],
                linewidth=2, color='darkgreen', label='Mean')
    axes[1].fill_between(df['repetition'],
                        df['fullness_mean'] - df['fullness_std'],
                        df['fullness_mean'] + df['fullness_std'],
                        alpha=0.2, color='green', label='±1 std')
    
    axes[1].set_xlabel('Repetition (sequence cycles)', fontsize=12)
    axes[1].set_ylabel('Snapshot Fullness', fontsize=12)
    axes[1].set_title('Convergence: Snapshot Fullness', fontsize=13, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=10)
    
    # Add super title
    fig.suptitle(f"B={B}, method={method}, p={p:.2f}, mean α={mean_alpha:.3f}", 
                fontsize=12, y=1.02)
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_convergence.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Plot 2: Zoomed detail (last 20%)
    cutoff = int(len(df) * 0.8)
    df_zoom = df.iloc[cutoff:]
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    ax.plot(df_zoom['repetition'], df_zoom['time_avg_fullness_mean'], 
           linewidth=2, color='red', marker='o', markersize=4, label='Mean')
    ax.fill_between(df_zoom['repetition'], 
                   df_zoom['time_avg_fullness_mean'] - df_zoom['time_avg_fullness_std'],
                   df_zoom['time_avg_fullness_mean'] + df_zoom['time_avg_fullness_std'],
                   alpha=0.2, color='red', label='±1 std')
    
    ax.set_xlabel('Repetition (sequence cycles)', fontsize=12)
    ax.set_ylabel('Time-Averaged Fullness', fontsize=12)
    ax.set_title(f'Convergence Detail (Last 20%)\nB={B}, method={method}, p={p:.2f}, mean α={mean_alpha:.3f}', 
                fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_convergence_detail.png', dpi=150, bbox_inches='tight')
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description='Analyze sequence simulation results and generate convergence plots',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze and generate plots
  python analyze_sequence_results.py aggregated_results.csv
  
  # From a run directory
  python ../../analyze/analyze_sequence_results.py my_results.csv

Output:
  Plots are automatically saved in the same directory as input CSV:
  - analysis_convergence.png: Full convergence plot (2 panels)
  - analysis_convergence_detail.png: Zoomed detail view (last 20%)
        """
    )
    
    parser.add_argument('csv_file', help='Aggregated CSV file from collect command')
    
    args = parser.parse_args()
    
    analyze_and_plot(args.csv_file)
    
    print(f"\n>>> Analysis complete!")


if __name__ == "__main__":
    main()

