#!/usr/bin/env python3
"""
Unified leaf splitting simulation framework.

Supports multiple splitting strategies:
- 'deferred': Split decision deferred until after batch insertion
- 'immediately': Split immediately when block reaches capacity
- 'adaptive': Adaptive split point based on insertion location (split at p or 1-p)
- 'adaptive2': Symmetric adaptive (split at 1-p if insertion at end, else p)
- 'phased': Phased strategy - uses p=0.5 for first N/16 elements, then p=0.49 (immediately split)

All methods use optimized histogram-based simulation.
"""

from typing import Any


import math
import random
from dataclasses import dataclass
import numpy as np

from typing import Sequence, List


@dataclass
class Stats:
    """Statistics tracking for simulation."""
    inserts: int = 0
    splits: int = 0
    moves: int = 0
    blocks_tally: int = 0
    elem_tally: int = 0
    capacity_tally: int = 0


# Module-level helper functions (can be reused by other modules)

def compute_split_size(n: int, p: float, rounding: str = "floor") -> tuple:
    """
    Compute split sizes for a block of size n.
    
    Parameters
    ----------
    n : int
        Block size to split
    p : float
        Split ratio (0.0 to 1.0)
    rounding : str
        'floor', 'ceil', or 'nearest'
    
    Returns
    -------
    tuple : (left_size, right_size)
    """
    raw = p * n
    if rounding == "floor":
        k = int(math.floor(raw))
    elif rounding == "ceil":
        k = int(math.ceil(raw))
    else:  # "nearest"
        k = int(round(raw))
    k = max(1, min(n - 1, k))
    return k, n - k


def sample_block_from_histogram(size_counts: dict):
    """
    Sample block with probability ∝ size, return (size, position).
    
    Parameters
    ----------
    size_counts : dict
        Histogram of block sizes {size: count}
    
    Returns
    -------
    tuple : (block_size, insert_position)
    """
    total_weight = sum(count * size for size, count in size_counts.items())
    if total_weight == 0:
        sizes = list[Any](size_counts.keys())
        return (random.choice(sizes), 0)
    
    rand_val = random.randint(0, total_weight - 1)
    cumsum = 0
    for size, count in size_counts.items():
        cumsum += count * size
        if rand_val < cumsum:
            within_class = rand_val - (cumsum - count * size)
            position = within_class % size if size > 0 else 0
            return (size, position)
    max_size = max(size_counts.keys())
    return (max_size, max_size // 2)


def insert_deferred_split(block_size: int, batch_size: int, B: int, p: float, rounding: str = "floor"):
    """
    Deferred split: insert batch, then check if split needed (with cascading).
    
    Parameters
    ----------
    block_size : int
        Current size of the block
    batch_size : int
        Number of elements to insert
    B : int
        Block capacity
    p : float
        Split ratio
    rounding : str
        Rounding method
    
    Returns
    -------
    tuple : (list of resulting block sizes, number of splits)
    """
    new_size = block_size + batch_size
    
    if new_size < B:
        return [new_size], 0
    
    blocks_to_split = [new_size]
    resulting_blocks = []
    num_splits = 0
    
    while blocks_to_split:
        current_size = blocks_to_split.pop(0)
        
        if current_size < B:
            resulting_blocks.append(current_size)
        else:
            left_size, right_size = compute_split_size(current_size, p, rounding)
            num_splits += 1
            
            if left_size >= B:
                blocks_to_split.append(left_size)
            else:
                resulting_blocks.append(left_size)
            
            if right_size >= B:
                blocks_to_split.append(right_size)
            else:
                resulting_blocks.append(right_size)
    
    return resulting_blocks, num_splits


def insert_with_position_split(
    block_size: int, insert_pos: int, batch_size: int, B: int, p: float, 
    method: str, rounding: str = "floor"
):
    """
    Split during insertion (for immediately, adaptive, adaptive2 methods).
    
    Parameters
    ----------
    block_size : int
        Current size of the block
    insert_pos : int
        Position where insertion starts
    batch_size : int
        Number of elements to insert
    B : int
        Block capacity
    p : float
        Split ratio
    method : str
        'immediately', 'adaptive', or 'adaptive2'
    rounding : str
        Rounding method
    
    Returns
    -------
    tuple : (list of resulting block sizes, number of splits)
    """
    current_size = block_size
    current_pos = insert_pos
    elements_remaining = batch_size
    resulting_blocks = []
    num_splits = 0
    
    while True:
        space_available = B - current_size
        
        if elements_remaining < space_available:
            current_size += elements_remaining
            resulting_blocks.append(current_size)
            break
        else:
            elements_to_insert = space_available
            current_size = B
            elements_remaining -= elements_to_insert
            
            insert_end_pos = current_pos + elements_to_insert
            
            # Determine split point based on method
            if method == 'immediately':
                left_size, right_size = compute_split_size(current_size, p, rounding)
            elif method == 'adaptive':
                raw_p = p * current_size
                p_split = max(1, min(current_size - 1, int(math.floor(raw_p))))
                
                if insert_end_pos < p_split:
                    left_size = p_split
                    right_size = current_size - p_split
                else:
                    left_size = current_size - p_split
                    right_size = p_split
            else:  # adaptive2
                raw_p = p * current_size
                p_split = max(1, min(current_size - 1, int(math.floor(raw_p))))
                one_minus_p_pos = current_size - p_split
                
                if insert_end_pos > one_minus_p_pos:
                    left_size = one_minus_p_pos
                    right_size = p_split
                else:
                    left_size = p_split
                    right_size = one_minus_p_pos
            
            if insert_end_pos < left_size:
                resulting_blocks.append(right_size)
                current_size = left_size
                current_pos = insert_end_pos
            else:
                resulting_blocks.append(left_size)
                current_size = right_size
                current_pos = insert_end_pos - left_size
            
            num_splits += 1
            
            if elements_remaining == 0:
                resulting_blocks.append(current_size)
                break
    
    return resulting_blocks, num_splits


def simulate(
    B: int,
    r: int,
    total_insertions: int,
    method: str = 'deferred',
    p: float = 0.5,
    rounding: str = "floor",
    seed=None,
    track_fullness_curve: bool = False,
):
    """
    Run leaf splitting simulation using histogram approach.
    
    Parameters
    ----------
    B : int
        Block capacity
    r : int
        Batch size (number of elements per batch)
    total_insertions : int
        Total number of elements to insert
    method : str
        Splitting method: 'deferred', 'immediately', 'adaptive', 'adaptive2', or 'phased'
        'phased': uses p=0.5 for first N/16 elements, then p=0.49 (immediately split)
    p : float
        Split ratio (for computing split position)
    rounding : str
        'floor', 'ceil', or 'nearest' for split position
    seed : int or None
        Random seed for reproducibility
    track_fullness_curve : bool
        If True, track instantaneous and time-averaged fullness at each batch
    
    Returns
    -------
    dict : Results with stats and metrics
        If track_fullness_curve=True, also includes:
        - 'fullness_curve': list of instantaneous fullness values
        - 'time_avg_fullness_curve': list of time-averaged fullness values
        - 'insertion_counts': list of total insertions at each measurement point
    """
    if seed is not None:
        random.seed(seed)
    
    assert r >= 1, "r must be >= 1"
    num_batches = total_insertions // r
    n = num_batches * r  # Actual total elements
    
    # Initialize size histogram with one empty block
    size_counts = {0: 1}
    total_keys = 0
    
    # Stats tracking
    stats = Stats()
    
    # Time series tracking (if requested)
    fullness_curve: List[float] | None = [] if track_fullness_curve else None
    time_avg_fullness_curve: List[float] | None = [] if track_fullness_curve else None
    sliding_window_avg_curve: List[float] | None = [] if track_fullness_curve else None
    
    # Sliding window for recent fullness values (10*B insertions)
    window_size = 10 * B  # Number of insertions in the window
    fullness_window: List[float] | None = [] if track_fullness_curve else None
    
    # Sampling interval: record every B//3 batches (and always at the end)
    sample_interval = max(1, B // 3) if track_fullness_curve else 1
    
    # Main simulation loop
    for batch_idx in range(num_batches):
        # Sample a block
        old_size, insert_pos = sample_block_from_histogram(size_counts)
        
        # Remove old block from histogram
        size_counts[old_size] -= 1
        if size_counts[old_size] == 0:
            del size_counts[old_size]
        
        # Insert batch using method-specific logic
        if method == 'deferred':
            new_blocks, num_splits = insert_deferred_split(old_size, r, B, p, rounding)
        elif method == 'phased':
            # Phased method: use p=0.5 for first N/16 elements, then p=0.49
            # Check before inserting this batch (total_keys is current count before this batch)
            threshold_1 = n / 32  # n is the actual total elements to be inserted
            threshold_2 = n / 8  # n is the actual total elements to be inserted
            current_p = 0.5 if total_keys < threshold_1 or total_keys > threshold_2 else 0.49
            new_blocks, num_splits = insert_with_position_split(
                old_size, insert_pos, r, B, current_p, 'immediately', rounding)
        elif method in ['immediately', 'adaptive', 'adaptive2']:
            new_blocks, num_splits = insert_with_position_split(
                old_size, insert_pos, r, B, p, method, rounding)
        else:
            raise ValueError(f"Unknown method '{method}'. Must be 'deferred', 'immediately', 'adaptive', 'adaptive2', or 'phased'.")
        
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
        
        # Record fullness metrics (always compute for sliding window, but only save at sample points)
        if track_fullness_curve:
            # Compute instantaneous fullness at every batch (for sliding window)
            if num_blocks > 0:
                current_fullness = total_keys / (B * num_blocks)
            else:
                current_fullness = 0.0
            
            # Add to sliding window (one value per insertion in the batch)
            for _ in range(r):
                fullness_window.append(current_fullness)
                # Keep only the last window_size values
                if len(fullness_window) > window_size:
                    fullness_window.pop(0)
            
            # Only save to curves at sample points
            is_last_batch = (batch_idx == num_batches - 1)
            should_sample = (batch_idx % sample_interval == 0) or is_last_batch
            
            if should_sample:
                # Instantaneous fullness
                fullness_curve.append(current_fullness)
                
                # Time-averaged fullness (cumulative average)
                if stats.capacity_tally > 0:
                    current_time_avg = stats.elem_tally / stats.capacity_tally
                else:
                    current_time_avg = 0.0
                time_avg_fullness_curve.append(current_time_avg)
                
                # Sliding window average (average of last 10*B insertions)
                if fullness_window:
                    window_avg = sum(fullness_window) / len(fullness_window)
                else:
                    window_avg = current_fullness  # Fallback if window not filled yet
                sliding_window_avg_curve.append(window_avg)
    
    # Final statistics
    final_blocks = sum(size_counts.values())
    final_fullness = n / (B * final_blocks) if final_blocks > 0 else 0.0
    time_avg_fullness = stats.elem_tally / stats.capacity_tally if stats.capacity_tally > 0 else 0.0
    
    # Method-specific stats
    if method == 'deferred':
        high_count = sum(count for size, count in size_counts.items() if size > B - r)
        frac_high = high_count / final_blocks if final_blocks > 0 else 0.0
        mu = total_keys / final_blocks if final_blocks > 0 else 0.0
        
        result = {
            "method": method,
            "stats": stats,
            "size_counts": size_counts,
            "final_blocks": final_blocks,
            "final_fullness": final_fullness,
            "time_avg_fullness": time_avg_fullness,
            "total_insertions": n,
            "k_H": frac_high,
            "k_L": 1 - frac_high,
            "mu": mu,
            "r": r,
            "B": B,
        }
        if track_fullness_curve:
            result["fullness_curve"] = fullness_curve
            result["time_avg_fullness_curve"] = time_avg_fullness_curve
            result["sliding_window_avg_curve"] = sliding_window_avg_curve
        return result
    else:  # immediately, adaptive, adaptive2, or phased
        result = {
            "method": method,
            "stats": stats,
            "size_counts": size_counts,
            "final_blocks": final_blocks,
            "final_fullness": final_fullness,
            "time_avg_fullness": time_avg_fullness,
            "total_insertions": n,
            "B": B,
            "r": r,
            "inserts": stats.inserts,
            "splits": stats.splits,
        }
        # For phased method, p is dynamic, so we don't include it
        if method != 'phased':
            result["p"] = p
        if track_fullness_curve:
            result["fullness_curve"] = fullness_curve
            result["time_avg_fullness_curve"] = time_avg_fullness_curve
            result["sliding_window_avg_curve"] = sliding_window_avg_curve
        return result



def simulate_variable_r(
    B: int,
    r_seq: Sequence[Sequence[int]],
    method: str = 'deferred',
    p: float = 0.5,
    rounding: str = "floor",
    seed=None,
    track_fullness_curve: bool = False,
):
    """
    Run leaf splitting simulation with a *variable* batch size schedule.

    r_seq is an "array of arrays", each block:
        [repeat, r1, r2, ...]
    meaning: repeat the pattern (r1, r2, ...) exactly `repeat` times.

    Example:
        r_seq = [
            [10000, 6, 7, 8],   # (6,7,8) repeated 10k times
            [5000, 20],         # then 20 repeated 5k times
        ]

    Parameters
    ----------
    B : int
        Block capacity.
    r_seq : sequence of sequences
        Schedule [[repeat, r1, r2, ...], ...].
    method : str
        'deferred', 'immediately', 'adaptive', or 'adaptive2'.
    p : float
        Split ratio.
    rounding : str
        'floor', 'ceil', or 'nearest'.
    seed : int or None
        Random seed.
    track_fullness_curve : bool
        If True, return 'fullness_curve' giving instantaneous fullness
        after each batch insertion.

    Returns
    -------
    dict
        Similar to `simulate`, but with:
          - 'total_insertions' = sum of all r_t
          - optionally 'fullness_curve'
          - 'schedule' = the compressed r_seq spec
    """
    if seed is not None:
        random.seed(seed)

    if not r_seq:
        raise ValueError("r_seq must be non-empty.")

    # Initialize size histogram with one empty block
    size_counts = {0: 1}
    total_keys = 0
    stats = Stats()

    fullness_curve: List[float] | None = [] if track_fullness_curve else None
    total_insertions = 0  # sum of all r_t

    # Main simulation: two nested loops, no expansion
    for block in r_seq:
        if not block:
            raise ValueError("Empty block in r_seq.")
        repeat = block[0]
        pattern = block[1:]

        if repeat <= 0:
            raise ValueError(f"Repeat count must be > 0, got {repeat}.")
        if not pattern:
            raise ValueError(
                "Each block must be [repeat, r1, r2, ...], got only a repeat."
            )

        for r in pattern:
            if r < 1:
                raise ValueError(f"Batch sizes must be >= 1, got {r}.")

        for _ in range(repeat):
            for r in pattern:
                # Sample a block
                old_size, insert_pos = sample_block_from_histogram(size_counts)

                # Remove old block from histogram
                size_counts[old_size] -= 1
                if size_counts[old_size] == 0:
                    del size_counts[old_size]

                # Insert batch according to method
                if method == 'deferred':
                    new_blocks, num_splits = insert_deferred_split(
                        old_size, r, B, p, rounding
                    )
                elif method in ['immediately', 'adaptive', 'adaptive2']:
                    new_blocks, num_splits = insert_with_position_split(
                        old_size, insert_pos, r, B, p, method, rounding
                    )
                else:
                    raise ValueError(
                        f"Unknown method '{method}'. Must be 'deferred', "
                        f"'immediately', 'adaptive', or 'adaptive2'."
                    )

                # Add resulting blocks back
                for size in new_blocks:
                    size_counts[size] = size_counts.get(size, 0) + 1

                # Update stats
                stats.inserts += r
                stats.splits += num_splits
                num_blocks = sum(size_counts.values())
                total_keys += r
                total_insertions += r

                stats.blocks_tally += num_blocks * r
                stats.elem_tally += total_keys * r
                stats.capacity_tally += B * num_blocks * r

                # Record instantaneous fullness, if requested
                if track_fullness_curve:
                    if num_blocks > 0:
                        current_fullness = total_keys / (B * num_blocks)
                    else:
                        current_fullness = 0.0
                    fullness_curve.append(current_fullness)

    # Final statistics
    final_blocks = sum(size_counts.values())
    final_fullness = (
        total_keys / (B * final_blocks) if final_blocks > 0 else 0.0
    )
    time_avg_fullness = (
        stats.elem_tally / stats.capacity_tally
        if stats.capacity_tally > 0
        else 0.0
    )

    # Method-specific extra stats (mirror your simulate)
    if method == 'deferred':
        high_count = sum(
            count for size, count in size_counts.items() if size > B - 1
        )
        frac_high = high_count / final_blocks if final_blocks > 0 else 0.0
        mu = total_keys / final_blocks if final_blocks > 0 else 0.0

        result: dict[str, Any] = {
            "method": method,
            "stats": stats,
            "size_counts": size_counts,
            "final_blocks": final_blocks,
            "final_fullness": final_fullness,
            "time_avg_fullness": time_avg_fullness,
            "total_insertions": total_insertions,
            "k_H": frac_high,
            "k_L": 1 - frac_high,
            "mu": mu,
            "B": B,
            "schedule": r_seq,
        }
    else:
        result = {
            "method": method,
            "stats": stats,
            "size_counts": size_counts,
            "final_blocks": final_blocks,
            "final_fullness": final_fullness,
            "time_avg_fullness": time_avg_fullness,
            "total_insertions": total_insertions,
            "B": B,
            "p": p,
            "inserts": stats.inserts,
            "splits": stats.splits,
            "schedule": r_seq,
        }

    if track_fullness_curve:
        result["fullness_curve"] = fullness_curve

    return result


if __name__ == "__main__":
    # Quick test of both methods
    print("Testing unified simulation framework...")
    print("=" * 70)
    
    # Test deferred method
    print("\nDeferred method:")
    result = simulate(B=120, r=60, total_insertions=60000, method='deferred', p=0.3, seed=42)
    print(f"  Final fullness: {result['final_fullness']:.4f}")
    print(f"  Time avg fullness: {result['time_avg_fullness']:.4f}")
    print(f"  Splits: {result['stats'].splits}")
    print(f"  k_H: {result['k_H']:.4f}")
    
    # Test immediately method
    print("\nImmediately method:")
    result = simulate(B=120, r=60, total_insertions=60000, method='immediately', p=0.3, seed=42)
    print(f"  Final fullness: {result['final_fullness']:.4f}")
    print(f"  Time avg fullness: {result['time_avg_fullness']:.4f}")
    print(f"  Splits: {result['stats'].splits}")
    
    # Test adaptive method
    print("\nAdaptive method:")
    result = simulate(B=120, r=60, total_insertions=60000, method='adaptive', p=0.3, seed=42)
    print(f"  Final fullness: {result['final_fullness']:.4f}")
    print(f"  Time avg fullness: {result['time_avg_fullness']:.4f}")
    print(f"  Splits: {result['stats'].splits}")
    
    print("\n" + "=" * 70)
    print("All three methods working!")

