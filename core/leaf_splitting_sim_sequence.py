#!/usr/bin/env python3
"""
Leaf splitting simulation with variable batch sizes (r_sequence).

This module supports specifying a sequence of different batch sizes for insertions,
using the efficient histogram-based approach with persistent state across r changes.

Imports helper functions from leaf_splitting_sim.py to avoid code duplication.
"""

import random
import argparse
import json
import sys
import os
from typing import List, Optional, Dict

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.leaf_splitting_sim import (
    Stats,
    sample_block_from_histogram,
    insert_deferred_split,
    insert_with_position_split
)


def simulate_with_r_sequence(
    B: int,
    r_sequence: List[int],
    method: str = 'immediately',
    p: float = 0.5,
    rounding: str = "floor",
    repetitions: int = 1,
    seed: Optional[int] = None,
    num_snapshots: int = 100,
) -> Dict:
    """
    Run simulation with a sequence of different batch sizes.
    
    Uses histogram-based approach with sample_block_from_histogram() for efficiency.
    Histogram state persists across different r values in the sequence.
    
    Parameters
    ----------
    B : int
        Block capacity
    r_sequence : List[int]
        Sequence of batch sizes, e.g., [1, 2, 5, 1, 3]
    method : str
        'deferred', 'immediately', 'adaptive', or 'adaptive2'
    p : float
        Split ratio
    rounding : str
        'floor', 'ceil', or 'nearest'
    repetitions : int
        How many times to repeat the r_sequence
    seed : int, optional
        Random seed for reproducibility
    num_snapshots : int, optional
        Number of fullness snapshots to record (default: 100)
    
    Returns
    -------
    dict : Simulation results including time series of fullness
    """
    if seed is not None:
        random.seed(seed)
    
    # Initialize histogram with one empty block
    size_counts = {0: 1}
    total_keys = 0
    
    # Stats tracking
    stats = Stats()
    
    # Snapshot tracking
    snapshot_interval = max(1, repetitions // num_snapshots)
    fullness_snapshots = []
    time_avg_fullness_snapshots = []
    repetition_points = []
    
    # Main simulation loop - iterate through r_sequence
    for rep in range(repetitions):
        for r in r_sequence:
            # Sample a block
            old_size, insert_pos = sample_block_from_histogram(size_counts)
            
            # Remove old block from histogram
            size_counts[old_size] -= 1
            if size_counts[old_size] == 0:
                del size_counts[old_size]
            
            # Insert batch using method-specific logic
            if method == 'deferred':
                new_blocks, num_splits = insert_deferred_split(old_size, r, B, p, rounding)
            elif method in ['immediately', 'adaptive', 'adaptive2']:
                new_blocks, num_splits = insert_with_position_split(
                    old_size, insert_pos, r, B, p, method, rounding)
            else:
                raise ValueError(f"Unknown method '{method}'. Must be 'deferred', 'immediately', 'adaptive', or 'adaptive2'.")
            
            # Add resulting blocks to histogram
            for size in new_blocks:
                size_counts[size] = size_counts.get(size, 0) + 1
            
            # Update stats
            stats.inserts += r
            stats.splits += num_splits
            num_blocks = sum(size_counts.values())
            total_keys += r
            stats.blocks_tally += num_blocks * r
            stats.elem_tally += total_keys * r
            stats.capacity_tally += B * num_blocks * r
        
        # Record snapshot at regular intervals (after completing each sequence repetition)
        if snapshot_interval == 1 or rep % snapshot_interval == 0 or rep == repetitions - 1:
            final_blocks_snap = sum(size_counts.values())
            n_snap = stats.inserts
            fullness_snap = n_snap / (B * final_blocks_snap) if final_blocks_snap > 0 else 0.0
            time_avg_fullness_snap = stats.elem_tally / stats.capacity_tally if stats.capacity_tally > 0 else 0.0
            
            fullness_snapshots.append(fullness_snap)
            time_avg_fullness_snapshots.append(time_avg_fullness_snap)
            repetition_points.append(rep + 1)  # 1-indexed for readability
    
    # Final statistics
    final_blocks = sum(size_counts.values())
    n = stats.inserts
    final_fullness = n / (B * final_blocks) if final_blocks > 0 else 0.0
    time_avg_fullness = stats.elem_tally / stats.capacity_tally if stats.capacity_tally > 0 else 0.0
    
    return {
        "method": method,
        "B": B,
        "p": p,
        "r_sequence": r_sequence,
        "repetitions": repetitions,
        "sequence_length": len(r_sequence),
        "total_insertions": n,
        "total_splits": stats.splits,
        "final_blocks": final_blocks,
        "final_fullness": final_fullness,
        "time_avg_fullness": time_avg_fullness,
        "size_counts": dict(size_counts),
        "stats": stats,
        # Time series data
        "fullness_snapshots": fullness_snapshots,
        "time_avg_fullness_snapshots": time_avg_fullness_snapshots,
        "repetition_points": repetition_points,
        "num_snapshots": len(fullness_snapshots),
    }


def read_config_from_file(filepath: str) -> Dict:
    """
    Read configuration from JSON file.
    
    Expected format:
    {
        "B": 10,
        "r_sequence": [1, 2, 5, 1, 3],
        "repetitions": 10,
        "method": "immediately",
        "p": 0.5,
        "rounding": "floor",
        "seed": 42
    }
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def write_config_to_file(config: Dict, filepath: str):
    """Write configuration to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)


def write_results_to_file(result: Dict, filepath: str):
    """Save simulation results to JSON file."""
    output = {
        'parameters': {
            'B': result['B'],
            'method': result['method'],
            'p': result['p'],
            'r_sequence': result['r_sequence'],
            'repetitions': result['repetitions'],
            'sequence_length': result['sequence_length'],
            'total_insertions': result['total_insertions'],
        },
        'results': {
            'total_splits': result['total_splits'],
            'final_blocks': result['final_blocks'],
            'final_fullness': result['final_fullness'],
            'time_avg_fullness': result['time_avg_fullness'],
        },
        'size_distribution': result['size_counts'],
    }
    
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)


def print_summary(result: Dict, verbose: bool = False):
    """Print simulation summary."""
    print("\n" + "=" * 70)
    print("SIMULATION SUMMARY (Variable r)")
    print("=" * 70)
    print(f"Method: {result['method']}")
    print(f"Block capacity (B): {result['B']}")
    print(f"Split ratio (p): {result['p']}")
    print(f"r_sequence: {result['r_sequence']}")
    print(f"Repetitions: {result['repetitions']}")
    print(f"Total insertions: {result['total_insertions']}")
    print()
    print(f"Total splits: {result['total_splits']}")
    print(f"Split rate: {result['total_splits'] / result['total_insertions']:.4f}")
    print()
    print(f"Final blocks: {result['final_blocks']}")
    print(f"Final fullness: {result['final_fullness']:.4f}")
    print(f"Time-avg fullness: {result['time_avg_fullness']:.4f}")
    
    if verbose and 'size_counts' in result:
        print("\nBlock size distribution:")
        for size in sorted(result['size_counts'].keys(), reverse=True):
            count = result['size_counts'][size]
            print(f"  Size {size:3d}: {count:4d} blocks")
    
    print("=" * 70)


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description='Leaf splitting simulation with variable batch sizes (uses histogram method)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run from config file
  python leaf_splitting_sim_sequence.py --config my_config.json

  # Quick test with command-line parameters
  python leaf_splitting_sim_sequence.py --B 10 --r-sequence 1 2 5 1 3 --repetitions 10 --method immediately --p 0.5 --seed 42

  # Generate example config
  python leaf_splitting_sim_sequence.py --generate-config --output example.json

Config file format:
{
  "B": 10,
  "r_sequence": [1, 2, 5, 1, 3],
  "repetitions": 10,
  "method": "immediately",
  "p": 0.5,
  "rounding": "floor",
  "seed": 42
}
        """
    )
    
    # Input modes
    parser.add_argument('--config', '-c', type=str,
                       help='Read configuration from JSON file')
    parser.add_argument('--generate-config', action='store_true',
                       help='Generate example config file')
    
    # Simulation parameters
    parser.add_argument('--B', type=int, default=10,
                       help='Block capacity (default: 10)')
    parser.add_argument('--r-sequence', nargs='+', type=int,
                       help='Sequence of batch sizes, e.g., --r-sequence 1 2 5 1 3')
    parser.add_argument('--repetitions', '-r', type=int, default=1,
                       help='Number of times to repeat r_sequence (default: 1)')
    parser.add_argument('--method', '-m', type=str,
                       choices=['deferred', 'immediately', 'adaptive', 'adaptive2'],
                       default='immediately',
                       help='Split method (default: immediately)')
    parser.add_argument('--p', type=float, default=0.5,
                       help='Split ratio (default: 0.5)')
    parser.add_argument('--rounding', type=str,
                       choices=['floor', 'ceil', 'nearest'],
                       default='floor',
                       help='Rounding method (default: floor)')
    parser.add_argument('--seed', '-s', type=int, default=None,
                       help='Random seed for reproducibility')
    
    # Output options
    parser.add_argument('--output', '-o', type=str,
                       help='Save results to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output')
    
    args = parser.parse_args()
    
    # Handle generate-config mode
    if args.generate_config:
        example_config = {
            "B": 10,
            "r_sequence": [1, 2, 5, 1, 3],
            "repetitions": 10,
            "method": "immediately",
            "p": 0.5,
            "rounding": "floor",
            "seed": 42
        }
        output_file = args.output or 'example_config.json'
        write_config_to_file(example_config, output_file)
        print(f"Generated example config: {output_file}")
        return
    
    # Get parameters
    if args.config:
        print(f"Reading configuration from: {args.config}")
        params = read_config_from_file(args.config)
    else:
        if args.r_sequence is None:
            parser.error("Must specify --config or --r-sequence")
        params = {
            'B': args.B,
            'r_sequence': args.r_sequence,
            'repetitions': args.repetitions,
            'method': args.method,
            'p': args.p,
            'rounding': args.rounding,
            'seed': args.seed,
        }
    
    # Validate r_sequence
    if 'r_sequence' not in params or not params['r_sequence']:
        parser.error("r_sequence must be specified and non-empty")
    
    # Run simulation
    print(f"\nRunning simulation with variable batch sizes (histogram method)...")
    print(f"Parameters: B={params['B']}, method={params['method']}, p={params.get('p', 'N/A')}")
    print(f"r_sequence: {params['r_sequence']}")
    print(f"Repetitions: {params.get('repetitions', 1)}")
    if params.get('seed'):
        print(f"Random seed: {params['seed']}")
    
    result = simulate_with_r_sequence(**params)
    
    # Print results
    print_summary(result, verbose=args.verbose)
    
    # Save if requested
    if args.output:
        write_results_to_file(result, args.output)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
