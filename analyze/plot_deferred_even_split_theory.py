"""
Plot comparison between theoretical and simulated values for deferred even split strategy.

For r ∈ [B/(2i), B/(2i-1)), the theoretical ratio is:
    (2ir/B) * H_{2i} - H_i

where H_i = 1 + 1/2 + ... + 1/i (harmonic number) and i is an integer.
"""

import csv
import argparse
import os
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple, Dict


def harmonic_number(n: int) -> float:
    """Calculate the nth harmonic number H_n = 1 + 1/2 + ... + 1/n."""
    if n <= 0:
        return 0.0
    return sum(1.0 / i for i in range(1, n + 1))


def theoretical_ratio(r: float, B: int) -> float:
    """
    Calculate theoretical time-averaged fullness for deferred even split.
    
    For r ∈ [B/(2i), B/(2i-1)), the formula is: (2ir/B) * (H_{2i} - H_i)
    where H_i = 1 + 1/2 + ... + 1/i (harmonic number)
    
    Note: This formula only applies to the range [B/(2i), B/(2i-1)).
    We do NOT have closed form for r ∈ [B/(2i-1), B/(2i-2)), so return None for those ranges.
    
    Parameters
    ----------
    r : float
        Batch size
    B : int
        Block capacity
    
    Returns
    -------
    float or None
        Theoretical time-averaged fullness, or None if r is not in a valid range
    """
    if r <= 0:
        return None
    
    # Find which interval r belongs to: r ∈ [B/(2i), B/(2i-1))
    # This means: B/(2i) <= r < B/(2i-1)
    # Rearranging: 2i <= B/r < 2i-1
    # So: B/r is in (2i-1, 2i]
    # This means: 2i-1 < B/r <= 2i
    # So: i-0.5 < B/(2r) <= i
    # Therefore: i = floor(B/(2r)) + 1, but we need to check boundaries
    
    # Calculate i by finding which range contains r
    # We'll check all possible i values to find the correct one
    i = None
    for test_i in range(1, int(B) + 1):
        test_lower = B / (2 * test_i)
        if test_i == 1:
            test_upper = B  # For i=1: [B/2, B)
        else:
            test_upper = B / (2 * test_i - 1)
        
        if test_lower <= r < test_upper:
            # For i=1, also check we're within our plotting range [1, B/2]
            if test_i == 1 and r > B / 2:
                continue
            i = test_i
            break
    
    if i is None:
        return None  # r is not in any valid range
    
    # Ensure i is at least 1
    i = max(1, i)
    
    # Verify r is in the correct interval [B/(2i), B/(2i-1))
    # Note: Formula only applies to these specific ranges, not others
    lower_bound = B / (2 * i)
    if i == 1:
        # For i=1: r ∈ [B/2, B/(2*1-1)) = [B/2, B)
        # But we only plot up to B/2, so for i=1 we only have r = B/2
        upper_bound = B
        if r < lower_bound or r >= upper_bound:
            return None
        # Since we only plot up to B/2, exclude r > B/2
        if r > B / 2:
            return None
    else:
        upper_bound = B / (2 * i - 1)
        if r < lower_bound or r >= upper_bound:
            # Try to find the correct i by checking all intervals
            found = False
            for test_i in range(1, int(B) + 1):
                test_lower = B / (2 * test_i)
                if test_i == 1:
                    test_upper = B  # For i=1: [B/2, B)
                else:
                    test_upper = B / (2 * test_i - 1)
                
                if test_lower <= r < test_upper:
                    # For i=1, also check we're within our plotting range [1, B/2]
                    if test_i == 1 and r > B / 2:
                        continue
                    i = test_i
                    found = True
                    break
            
            if not found:
                return None  # r is not in any valid range with closed form
    
    # Calculate H_{2i} and H_i
    H_2i = harmonic_number(2 * i)
    H_i = harmonic_number(i)
    
    # Calculate time-averaged fullness: (2ir/B) * (H_{2i} - H_i)
    fullness = (2 * i * r / B) * (H_2i - H_i)
    
    return fullness


def load_simulation_data(csv_file: str, B: int, method: str = 'deferred', metric: str = 'time_avg') -> List[Tuple[float, float]]:
    """
    Load simulation data from CSV file for even split (p=0.5).
    
    Parameters
    ----------
    csv_file : str
        Path to CSV file with simulation results
    B : int
        Block capacity to filter by
    method : str
        Method to filter by (default: 'deferred')
    metric : str
        Metric to load: 'time_avg' for time-averaged fullness or 'final' for final fullness
    
    Returns
    -------
    list of tuples
        List of (r, fullness) pairs
    """
    results = []
    p = 0.5  # Even split always uses p=0.5
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_B = int(float(row.get('B', 0)))
            row_p = float(row.get('p', 0))
            row_r = int(float(row.get('r', 0)))
            
            # Filter by B and p=0.5 (even split)
            # Note: CSV files from deferred runs don't have method column, 
            # but the file is from a deferred run directory
            if row_B == B and abs(row_p - p) < 0.001:
                if metric == 'final':
                    # Final fullness is given by fullness_mean in the CSV
                    fullness = float(row.get('fullness_mean', 0))
                else:  # time_avg
                    # Time-averaged fullness is given by time_avg_fullness_mean in the CSV
                    fullness = float(row.get('time_avg_fullness_mean', 0))
                results.append((row_r, fullness))
    
    # Sort by r
    results.sort(key=lambda x: x[0])
    return results


def plot_comparison(csv_file: str, B: int, save_dir: str = None, metric: str = 'time_avg'):
    """
    Plot comparison between theoretical and simulated values for deferred even split.
    
    Parameters
    ----------
    csv_file : str
        Path to CSV file with simulation results
    B : int
        Block capacity
    save_dir : str
        Directory to save the plot (default: same as CSV file)
    metric : str
        Metric to plot: 'time_avg' for time-averaged fullness or 'final' for final fullness
        Note: Theoretical formula only applies to time-averaged fullness
    """
    p = 0.5  # Even split always uses p=0.5
    
    # Load simulation data
    print(f"Loading simulation data from {csv_file}...")
    sim_data = load_simulation_data(csv_file, B, method='deferred', metric=metric)
    
    if not sim_data:
        print(f"Error: No simulation data found for B={B}, p={p} (even split), metric={metric}")
        print(f"Make sure the CSV file contains data for B={B} and p=0.5")
        return
    
    print(f"Found {len(sim_data)} data points")
    
    # Extract r values and simulation values
    r_sim = [x[0] for x in sim_data]
    fullness_sim = [x[1] for x in sim_data]
    
    # Filter to r in [1, B/2]
    filtered_data = [(r, f) for r, f in zip(r_sim, fullness_sim) if 1 <= r <= B / 2]
    r_sim = [x[0] for x in filtered_data]
    fullness_sim = [x[1] for x in filtered_data]
    
    if not r_sim:
        print(f"Error: No data points in range r ∈ [1, {B/2}]")
        return
    
    # Calculate theoretical values for the same r values
    r_theory = []
    fullness_theory = []
    for r in sorted(set(r_sim)):
        theory_val = theoretical_ratio(r, B)
        if theory_val is not None:
            r_theory.append(r)
            fullness_theory.append(theory_val)
    
    # Also create a smooth curve for theoretical values (only in valid ranges)
    # We only draw theory line for r ∈ [B/(2i), B/(2i-1))
    # We do NOT draw for r ∈ [B/(2i-1), B/(2i-2)) as we don't have closed form
    # Store segments separately to avoid connecting across invalid ranges
    segments = []
    
    # Generate points for each valid range [B/(2i), B/(2i-1))
    # IMPORTANT: We only draw for [B/(2i), B/(2i-1)), NOT for [B/(2i-1), B/(2i-2))
    for i in range(1, int(B) + 1):
        lower = B / (2 * i)
        if i == 1:
            # For i=1: range is [B/2, B), but we only plot up to B/2
            upper = B / 2
        else:
            # For i>1: range is [B/(2i), B/(2i-1))
            # We must be careful: upper bound is B/(2i-1), which is EXCLUSIVE
            upper = B / (2 * i - 1)
        
        # Only include if the range overlaps with [1, B/2]
        if upper > 1 and lower < B / 2:
            # Create points in this range, but ensure we don't exceed the upper bound
            range_lower = max(1, lower)
            # For the upper bound: range is [B/(2i), B/(2i-1)), so B/(2i-1) is EXCLUSIVE
            # We'll use endpoint=False in np.linspace to ensure we don't include the upper bound
            range_upper = min(B / 2, upper)
            
            if range_lower < range_upper:
                # Generate points for this valid range segment
                # IMPORTANT: Range is [B/(2i), B/(2i-1)), which is left-closed, right-open
                # So we must NOT include the upper bound B/(2i-1)
                if i == 1:
                    # For i=1, we already limited to B/2, and B/2 is the lower bound
                    # So we can use the full range
                    r_range = np.linspace(range_lower, range_upper, 100, endpoint=False)
                else:
                    # For i>1: range is [B/(2i), B/(2i-1))
                    # We must exclude the upper bound B/(2i-1)
                    # Use endpoint=False to exclude the upper bound
                    r_range = np.linspace(range_lower, range_upper, 100, endpoint=False)
                
                # Collect points for this segment
                segment_r = []
                segment_f = []
                for r in r_range:
                    # Double-check that the value is valid before adding
                    theory_val = theoretical_ratio(r, B)
                    if theory_val is not None:
                        segment_r.append(r)
                        segment_f.append(theory_val)
                
                # Add this segment if it has points
                if segment_r:
                    segments.append((segment_r, segment_f))
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot theoretical curve (red line) - use the same curve for both metrics
    # Note: Theoretical formula is for time-averaged fullness, but we plot it for final too as reference
    if segments:
        # Plot each segment separately (each segment is one valid range)
        for seg_r, seg_f in segments:
            ax.plot(seg_r, seg_f, 'r-', linewidth=2, alpha=0.8)
        
        # Add label only once
        ax.plot([], [], 'r-', linewidth=2, label='Theoretical (closed form)', alpha=0.8)
    
    # Plot simulation data (blue markers)
    ax.plot(r_sim, fullness_sim, 'bo', markersize=6, label='Simulation', alpha=0.7)
    
    ax.set_xlabel('r (batch size)', fontsize=14)
    if metric == 'final':
        ax.set_ylabel('Final Fullness', fontsize=14)
        ax.set_title(f'Deferred Even Split: Final Fullness vs Theory\nB={B}, p=0.5, r ∈ [1, {B//2}]', fontsize=14)
    else:
        ax.set_ylabel('Time-Averaged Fullness', fontsize=14)
        ax.set_title(f'Deferred Even Split: Theory vs Simulation\nB={B}, p=0.5, r ∈ [1, {B//2}]', fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0, right=B/2 + 1)
    
    plt.tight_layout()
    
    # Save plot
    if save_dir is None:
        save_dir = os.path.dirname(os.path.abspath(csv_file))
    os.makedirs(save_dir, exist_ok=True)
    
    metric_suffix = 'final' if metric == 'final' else 'timeavg'
    filename = os.path.join(save_dir, f'deferred_even_split_theory_vs_sim_B{B}_{metric_suffix}.png')
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved plot to: {filename}")
    
    # Also save data for reference
    data_file = os.path.join(save_dir, f'deferred_even_split_comparison_B{B}_{metric_suffix}.csv')
    with open(data_file, 'w', newline='') as f:
        writer = csv.writer(f)
        # Include theoretical values for both metrics
        writer.writerow(['r', 'simulation_fullness', 'theoretical_fullness'])
        for r in sorted(set(r_sim)):
            sim_val = next((f for r_val, f in zip(r_sim, fullness_sim) if r_val == r), None)
            theory_val = theoretical_ratio(r, B)
            if sim_val is not None:
                writer.writerow([r, sim_val, theory_val if theory_val is not None else ''])
    print(f"Saved comparison data to: {data_file}")
    
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description='Plot comparison between theoretical and simulated values for deferred even split'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to CSV file with simulation results'
    )
    parser.add_argument(
        '--B',
        type=int,
        required=True,
        help='Block capacity'
    )
    parser.add_argument(
        '--metric',
        type=str,
        default='time_avg',
        choices=['time_avg', 'final'],
        help='Metric to plot: time_avg (time-averaged fullness) or final (final fullness). Default: time_avg'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default=None,
        help='Directory to save output (default: same as input file)'
    )
    
    args = parser.parse_args()
    
    plot_comparison(args.input, args.B, args.output_dir, args.metric)


if __name__ == "__main__":
    main()

