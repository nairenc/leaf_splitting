#!/usr/bin/env python3
"""
Plot convergence from aggregated sequence simulation results.

Expects aggregated CSV with one row per repetition point.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import sys


def plot_convergence(csv_file):
    """
    Plot convergence of fullness over time.
    
    Plot is automatically saved in the same directory as the input CSV
    as "convergence.png".
    
    Parameters
    ----------
    csv_file : str
        Path to aggregated CSV file (one row per repetition)
    """
    import os
    
    df = pd.read_csv(csv_file)
    df_sorted = df.sort_values('repetition')
    
    # Determine output file (same folder as input, name "convergence.png")
    input_dir = os.path.dirname(csv_file)
    if input_dir:
        output_file = os.path.join(input_dir, 'convergence.png')
    else:
        output_file = 'convergence.png'
    
    # Extract configuration
    first_row = df.iloc[0]
    B = int(first_row['B'])
    method = first_row['method']
    p = float(first_row['p'])
    mean_alpha = float(first_row['mean_alpha'])
    n_seeds = int(first_row['n_seeds']) if 'n_seeds' in first_row else "unknown"
    
    print(f"Loaded {len(df)} time points (aggregated across {n_seeds} seeds)")
    print(f"Configuration: B={B}, method={method}, p={p:.3f}, mean α={mean_alpha:.3f}")
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Time-averaged fullness
    ax1.plot(df_sorted['repetition'], df_sorted['time_avg_fullness_mean'], 
            linewidth=2, color='red', label='Mean')
    ax1.fill_between(df_sorted['repetition'], 
                    df_sorted['time_avg_fullness_mean'] - df_sorted['time_avg_fullness_std'],
                    df_sorted['time_avg_fullness_mean'] + df_sorted['time_avg_fullness_std'],
                    alpha=0.2, color='red', label='±1 std')
    
    ax1.set_xlabel('Repetition (sequence cycles)', fontsize=12)
    ax1.set_ylabel('Time-Averaged Fullness', fontsize=12)
    ax1.set_title('Convergence: Time-Averaged Fullness', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot 2: Snapshot fullness
    ax2.plot(df_sorted['repetition'], df_sorted['fullness_mean'],
            linewidth=2, color='darkgreen', label='Mean')
    ax2.fill_between(df_sorted['repetition'],
                    df_sorted['fullness_mean'] - df_sorted['fullness_std'],
                    df_sorted['fullness_mean'] + df_sorted['fullness_std'],
                    alpha=0.2, color='green', label='±1 std')
    
    ax2.set_xlabel('Repetition (sequence cycles)', fontsize=12)
    ax2.set_ylabel('Snapshot Fullness', fontsize=12)
    ax2.set_title('Convergence: Snapshot Fullness', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Add super title
    fig.suptitle(f"B={B}, method={method}, p={p:.2f}, mean α={mean_alpha:.3f}", 
                fontsize=12, y=1.02)
    
    plt.tight_layout()
    
    # Save plot
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nSaved plot to: {output_file}")
    plt.close()
    
    # Print convergence statistics
    final_time_avg = df_sorted.iloc[-1]['time_avg_fullness_mean']
    final_std = df_sorted.iloc[-1]['time_avg_fullness_std']
    
    print(f"\nFinal time-avg fullness: {final_time_avg:.6f} ± {final_std:.6f}")
    
    # Check convergence
    if len(df_sorted) >= 2:
        penultimate = df_sorted.iloc[-2]
        change = abs(df_sorted.iloc[-1]['time_avg_fullness_mean'] - penultimate['time_avg_fullness_mean'])
        print(f"Change in last interval: {change:.8f}")
        if change < 0.0001:
            print("OK: Converged")
        else:
            print("CAUTION: May need more repetitions")


def main():
    parser = argparse.ArgumentParser(
        description='Plot convergence from aggregated sequence simulation results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate convergence plot
  python plot_convergence.py aggregated_results.csv
  
  # From a run directory
  python ../../analyze/plot_convergence.py my_results.csv

Output:
  Automatically saved in same directory as input CSV:
  - convergence.png (2-panel plot)

Input:
  Expects aggregated CSV from collect command with columns:
  - repetition
  - fullness_mean, fullness_std
  - time_avg_fullness_mean, time_avg_fullness_std
        """
    )
    
    parser.add_argument('csv_file', help='Aggregated CSV file from collect command')
    
    args = parser.parse_args()
    
    plot_convergence(args.csv_file)
    print("\n>>> Plot complete!")


if __name__ == "__main__":
    main()
