#!/usr/bin/env python3
"""
Unified leaf splitting simulation framework.

Supports multiple splitting strategies:
- 'deferred': Split decision deferred until after batch insertion
- 'immediately': Split immediately when block reaches capacity
- 'adaptive': Adaptive split point based on insertion location (split at p or 1-p)
- 'adaptive2': Symmetric adaptive (split at 1-p if insertion at end, else p)

All methods use optimized histogram-based simulation.
"""

import math
import random
from dataclasses import dataclass
import numpy as np


@dataclass
class Stats:
    """Statistics tracking for simulation."""
    inserts: int = 0
    splits: int = 0
    moves: int = 0
    blocks_tally: int = 0
    elem_tally: int = 0
    capacity_tally: int = 0


def simulate(
    B: int,
    r: int,
    total_insertions: int,
    method: str = 'deferred',
    p: float = 0.5,
    rounding: str = "floor",
    seed=None,
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
        Splitting method: 'deferred', 'immediately', 'adaptive', or 'adaptive2'
    p : float
        Split ratio (for computing split position)
    rounding : str
        'floor', 'ceil', or 'nearest' for split position
    seed : int or None
        Random seed for reproducibility
    
    Returns
    -------
    dict : Results with stats and metrics
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
    
    # Helper functions
    def split_size(n: int) -> tuple:
        """Compute split sizes for a block of size n."""
        raw = p * n
        if rounding == "floor":
            k = int(math.floor(raw))
        elif rounding == "ceil":
            k = int(math.ceil(raw))
        else:  # "nearest"
            k = int(round(raw))
        k = max(1, min(n - 1, k))
        return k, n - k
    
    # Sampling functions

    def sample_block():
        """Sample block with probability ∝ size, return position."""
        total_weight = sum(count * size for size, count in size_counts.items())
        if total_weight == 0:
            sizes = list(size_counts.keys())
            return (random.choice(sizes), 0)
        
        rand_val = random.randint(0, total_weight - 1)
        cumsum = 0
        for size, count in size_counts.items():
            cumsum += count * size
            if rand_val < cumsum:
                within_class = rand_val - (cumsum - count * size)
                # A block with 'size' keys has 'size' insertion positions (0 to size-1)
                # Position 'size' would belong to the next block in B-tree navigation
                position = within_class % size if size > 0 else 0
                return (size, position)
        max_size = max(size_counts.keys())
        return (max_size, max_size // 2)
    
    # Insertion functions
    def insert_deferred(block_size, batch_size):
        """Deferred split: insert r, then check if split needed (with cascading)."""
        new_size = block_size + batch_size
        
        if new_size < B:
            # No split needed
            return [new_size], 0
        
        # Split needed - handle cascading splits
        blocks_to_split = [new_size]
        resulting_blocks = []
        num_splits = 0
        
        while blocks_to_split:
            current_size = blocks_to_split.pop(0)
            
            if current_size < B:
                # This block doesn't need splitting
                resulting_blocks.append(current_size)
            else:
                # Split this block
                left_size, right_size = split_size(current_size)
                num_splits += 1
                
                # Check if resulting blocks need further splitting
                if left_size >= B:
                    blocks_to_split.append(left_size)
                else:
                    resulting_blocks.append(left_size)
                
                if right_size >= B:
                    blocks_to_split.append(right_size)
                else:
                    resulting_blocks.append(right_size)
        
        return resulting_blocks, num_splits
    
    def insert_immediately(block_size, insert_pos, batch_size):
        """Immediately split: split during insertion when block fills."""
        current_size = block_size
        current_pos = insert_pos
        elements_remaining = batch_size
        resulting_blocks = []
        num_splits = 0
        
        while True:
            space_available = B - current_size
            
            if elements_remaining < space_available:
                # All remaining elements fit without reaching capacity
                current_size += elements_remaining
                resulting_blocks.append(current_size)
                break
            elif elements_remaining == space_available:
                # Block fills exactly to capacity and must split
                current_size = B
                elements_remaining = 0
                
                left_size, right_size = split_size(current_size)
                insert_end_pos = current_pos + space_available
                
                if insert_end_pos <= left_size:
                    # All inserted elements in left child
                    resulting_blocks.append(left_size)
                    resulting_blocks.append(right_size)
                    break
                else:
                    # Insertion spans into right child, continue with right
                    resulting_blocks.append(left_size)
                    current_size = right_size
                    current_pos = insert_end_pos - left_size
                    # Continue loop in case right child is also full
                
                num_splits += 1
            else:
                # Block overflows: fill to capacity, split, and continue
                elements_to_insert = space_available
                current_size = B
                elements_remaining -= elements_to_insert
                
                left_size, right_size = split_size(current_size)
                insert_end_pos = current_pos + elements_to_insert
                
                if insert_end_pos <= left_size:
                    # Insertion is in left child, continue there
                    resulting_blocks.append(right_size)  # Right child is done
                    current_size = left_size
                    current_pos = insert_end_pos  # Continue from where we left off
                else:
                    # Insertion spans into right child, continue there
                    resulting_blocks.append(left_size)  # Left child is done
                    current_size = right_size
                    current_pos = insert_end_pos - left_size  # Position in right child coordinates
                
                num_splits += 1
        
        return resulting_blocks, num_splits
    
    def insert_adaptive(block_size, insert_pos, batch_size):
        """Adaptive split: choose split point based on insertion location."""
        current_size = block_size
        current_pos = insert_pos
        elements_remaining = batch_size
        resulting_blocks = []
        num_splits = 0
        
        while True:
            space_available = B - current_size
            
            if elements_remaining < space_available:
                # All remaining elements fit without reaching capacity
                current_size += elements_remaining
                resulting_blocks.append(current_size)
                break
            elif elements_remaining == space_available:
                # Block fills exactly to capacity and must split
                current_size = B
                elements_remaining = 0
                
                insert_end_pos = current_pos + space_available
                
                # Adaptive split: choose split point based on insertion location
                raw_p = p * current_size
                p_split = max(1, min(current_size - 1, int(math.floor(raw_p))))
                
                if insert_end_pos < p_split:
                    # Insertion in left part: split at p
                    left_size = p_split
                    right_size = current_size - p_split
                else:
                    # Insertion in right part: split at (1-p) to keep inserted elements in larger block
                    left_size = current_size - p_split
                    right_size = p_split
                
                if insert_end_pos <= left_size:
                    # All inserted elements in left child
                    resulting_blocks.append(left_size)
                    resulting_blocks.append(right_size)
                    break
                else:
                    # Insertion spans into right child, continue with right
                    resulting_blocks.append(left_size)
                    current_size = right_size
                    current_pos = insert_end_pos - left_size
                    # Continue loop in case right child is also full
                
                num_splits += 1
            else:
                # Block overflows: fill to capacity, split, and continue
                elements_to_insert = space_available
                current_size = B
                elements_remaining -= elements_to_insert
                
                insert_end_pos = current_pos + elements_to_insert
                
                # Adaptive split: choose split point based on insertion location
                raw_p = p * current_size
                p_split = max(1, min(current_size - 1, int(math.floor(raw_p))))
                
                if insert_end_pos < p_split:
                    # Insertion in left part: split at p
                    left_size = p_split
                    right_size = current_size - p_split
                else:
                    # Insertion in right part: split at (1-p)
                    left_size = current_size - p_split
                    right_size = p_split
                
                if insert_end_pos <= left_size:
                    # Insertion is in left child, continue there
                    resulting_blocks.append(right_size)  # Right child is done
                    current_size = left_size
                    current_pos = insert_end_pos  # Continue from where we left off
                else:
                    # Insertion spans into right child, continue there
                    resulting_blocks.append(left_size)  # Left child is done
                    current_size = right_size
                    current_pos = insert_end_pos - left_size  # Position in right child coordinates
                
                num_splits += 1
        
        return resulting_blocks, num_splits
    
    def insert_adaptive2(block_size, insert_pos, batch_size):
        """Adaptive2 split: symmetric version - split at (1-p) if insertion at end."""
        current_size = block_size
        current_pos = insert_pos
        elements_remaining = batch_size
        resulting_blocks = []
        num_splits = 0
        
        while True:
            space_available = B - current_size
            
            if elements_remaining < space_available:
                # All remaining elements fit without reaching capacity
                current_size += elements_remaining
                resulting_blocks.append(current_size)
                break
            elif elements_remaining == space_available:
                # Block fills exactly to capacity and must split
                current_size = B
                elements_remaining = 0
                
                insert_end_pos = current_pos + space_available
                
                # Adaptive2 split: SYMMETRIC - choose based on (1-p) threshold
                raw_p = p * current_size
                p_split = max(1, min(current_size - 1, int(math.floor(raw_p))))
                one_minus_p_pos = current_size - p_split
                
                if insert_end_pos > one_minus_p_pos:
                    # Insertion in right part (after (1-p)): split at (1-p)
                    left_size = one_minus_p_pos
                    right_size = p_split
                else:
                    # Insertion in left/middle part: split at p (default)
                    left_size = p_split
                    right_size = one_minus_p_pos
                
                if insert_end_pos <= left_size:
                    # All inserted elements in left child
                    resulting_blocks.append(left_size)
                    resulting_blocks.append(right_size)
                    break
                else:
                    # Insertion spans into right child, continue with right
                    resulting_blocks.append(left_size)
                    current_size = right_size
                    current_pos = insert_end_pos - left_size
                    # Continue loop in case right child is also full
                
                num_splits += 1
            else:
                # Block overflows: fill to capacity, split, and continue
                elements_to_insert = space_available
                current_size = B
                elements_remaining -= elements_to_insert
                
                insert_end_pos = current_pos + elements_to_insert
                
                # Adaptive2 split: SYMMETRIC - choose based on (1-p) threshold
                raw_p = p * current_size
                p_split = max(1, min(current_size - 1, int(math.floor(raw_p))))
                one_minus_p_pos = current_size - p_split
                
                if insert_end_pos > one_minus_p_pos:
                    # Insertion in right part: split at (1-p)
                    left_size = one_minus_p_pos
                    right_size = p_split
                else:
                    # Insertion in left/middle part: split at p
                    left_size = p_split
                    right_size = one_minus_p_pos
                
                if insert_end_pos <= left_size:
                    # Insertion is in left child, continue there
                    resulting_blocks.append(right_size)  # Right child is done
                    current_size = left_size
                    current_pos = insert_end_pos  # Continue from where we left off
                else:
                    # Insertion spans into right child, continue there
                    resulting_blocks.append(left_size)  # Left child is done
                    current_size = right_size
                    current_pos = insert_end_pos - left_size  # Position in right child coordinates
                
                num_splits += 1
        
        return resulting_blocks, num_splits
    
    # Main simulation loop
    for batch_idx in range(num_batches):
        # Sample a block
        old_size, insert_pos = sample_block()


        
        # Remove old block from histogram
        size_counts[old_size] -= 1
        if size_counts[old_size] == 0:
            del size_counts[old_size]
        
        # Insert batch using method-specific logic
        if method == 'deferred':
            new_blocks, num_splits = insert_deferred(old_size, r)
        elif method == 'adaptive':
            new_blocks, num_splits = insert_adaptive(old_size, insert_pos, r)
        elif method == 'adaptive2':
            new_blocks, num_splits = insert_adaptive2(old_size, insert_pos, r)
        elif method == 'immediately':
            new_blocks, num_splits = insert_immediately(old_size, insert_pos, r)
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
    
    # Final statistics
    final_blocks = sum(size_counts.values())
    final_fullness = n / (B * final_blocks) if final_blocks > 0 else 0.0
    time_avg_fullness = stats.elem_tally / stats.capacity_tally if stats.capacity_tally > 0 else 0.0
    
    # Method-specific stats
    if method == 'deferred':
        high_count = sum(count for size, count in size_counts.items() if size > B - r)
        frac_high = high_count / final_blocks if final_blocks > 0 else 0.0
        mu = total_keys / final_blocks if final_blocks > 0 else 0.0
        
        return {
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
    else:  # immediately or adaptive
        return {
            "method": method,
            "stats": stats,
            "size_counts": size_counts,
            "final_blocks": final_blocks,
            "final_fullness": final_fullness,
            "time_avg_fullness": time_avg_fullness,
            "total_insertions": n,
            "B": B,
            "r": r,
            "p": p,
            "inserts": stats.inserts,
            "splits": stats.splits,
        }


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

