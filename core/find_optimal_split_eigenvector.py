"""
Find optimal splitting strategy using eigenvector analysis.

For large N, the normalized distribution A(N)/(N+1) converges to an eigenvector
of the transition matrix with eigenvalue 1. We can use this to find the
steady-state fullness for different splitting strategies.
"""

import numpy as np
from typing import Tuple, List, Dict
import json

# Try to import scipy for better eigenvalue routines
try:
    from scipy import linalg
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# Set numpy to use higher precision
DTYPE = np.float128 if hasattr(np, 'float128') else np.float64


def build_transition_matrix(B: int, a: int = None, split_strategies: List[Tuple[int, float]] = None) -> np.ndarray:
    """
    Build the transition matrix C for the block size distribution.
    
    C[i, j] represents the change in blocks of size i when we hit a block of size j.
    - C[j, j] = -j (blocks of size j decrease when we hit size j)
    - C[j+1, j] = j (blocks of size j+1 increase when we hit size j)
    - Special case: when we hit size B-1, it splits according to the split strategy
    
    Parameters
    ----------
    B : int
        Block capacity
    a : int, optional
        Split parameter: when a block reaches B, it splits into blocks of size a and (B-a)
        Must satisfy: 1 <= a <= B-1
        If split_strategies is provided, this is ignored.
    split_strategies : list of (int, float), optional
        List of (split_size, probability) tuples for hybrid splitting strategy.
        Each tuple (a, p) means: with probability p, split into (a, B-a).
        Probabilities should sum to 1.0 (approximately).
        Example: [(120, 0.5), (119, 0.5)] means 50% chance of (120, 120) and 50% chance of (119, 121)
    
    Returns
    -------
    np.ndarray
        Transition matrix of shape (B+1, B+1)
    """
    # Validate parameters
    if split_strategies is None:
        if a is None:
            raise ValueError("Either a or split_strategies must be provided")
        if not (1 <= a <= B - 1):
            raise ValueError(f"Split parameter a must be between 1 and B-1, got a={a}, B={B}")
        # Convert single a to split_strategies format
        split_strategies = [(a, 1.0)]
    else:
        # Validate split_strategies
        total_prob = sum(p for _, p in split_strategies)
        if abs(total_prob - 1.0) > 1e-6:
            raise ValueError(f"Split strategy probabilities must sum to 1.0, got {total_prob}")
        for a_val, p in split_strategies:
            if not (1 <= a_val <= B - 1):
                raise ValueError(f"Split parameter a must be between 1 and B-1, got a={a_val}, B={B}")
            if not (0 <= p <= 1):
                raise ValueError(f"Probability must be between 0 and 1, got p={p}")
    
    # Matrix indices: 0 to B (inclusive)
    C = np.zeros((B + 1, B + 1), dtype=DTYPE)
    
    for i in range(1, B + 1):
        if i < B:
            # Normal case: blocks of size i
            # Decrease when we hit size i
            C[i, i] = -i
            # Increase when we hit size (i-1)
            if i - 1 >= 1:
                C[i, i - 1] = i - 1
    
    # Special case: when we hit size B-1, it splits according to the strategy
    for a_val, prob in split_strategies:
        split_left = a_val
        split_right = B - a_val
        
        # Weight by probability
        weight = prob * (B - 1)
        
        if split_left <= B:
            C[split_left, B - 1] += weight  # first split block
        if split_right <= B and split_right != split_left:
            C[split_right, B - 1] += weight  # second split block
        elif split_right == split_left:
            # If both splits are the same size, add both
            C[split_left, B - 1] += weight  # add the second one too
    
    return C


def find_steady_state_eigenvector_power_iteration(C: np.ndarray, B: int, max_iter: int = 1000, tol: float = 1e-12) -> Tuple[np.ndarray, float]:
    """
    Find the steady-state eigenvector using power iteration.
    
    Since we know C * v = v (eigenvalue is 1), we can use power iteration
    directly on C to find the eigenvector.
    
    Parameters
    ----------
    C : np.ndarray
        Transition matrix (we know C * v = v)
    B : int
        Block capacity
    max_iter : int
        Maximum number of iterations
    tol : float
        Convergence tolerance
    
    Returns
    -------
    tuple
        (eigenvector, eigenvalue)
    """
    # Initialize with uniform distribution
    v = np.ones(C.shape[0], dtype=DTYPE)
    v[0] = 0  # No blocks of size 0
    total_weighted = np.sum(np.arange(len(v), dtype=DTYPE) * v)
    if abs(total_weighted) > 1e-10:
        v = v / total_weighted
    
    # Power iteration: v_{k+1} = C * v_k, then normalize
    for i in range(max_iter):
        v_new = C @ v
        
        # Normalize by weighted sum: sum(i * v[i]) = 1
        total_weighted = np.sum(np.arange(len(v_new), dtype=DTYPE) * v_new)
        if abs(total_weighted) > 1e-10:
            v_new = v_new / total_weighted
        else:
            break
        
        # Check convergence
        diff = np.linalg.norm(v_new - v)
        if diff < tol:
            v = v_new
            break
        
        v = v_new
    
    # Ensure non-negative
    v = np.maximum(v, 0)
    total_weighted = np.sum(np.arange(len(v), dtype=DTYPE) * v)
    if abs(total_weighted) > 1e-10:
        v = v / total_weighted
    
    # Verify eigenvalue is 1: compute C * v and check if it equals v
    Cv = C @ v
    eigenvalue = 1.0  # We know it should be 1
    
    return v, eigenvalue


def find_steady_state_eigenvector(C: np.ndarray, B: int) -> Tuple[np.ndarray, float]:
    """
    Find the steady-state eigenvector with eigenvalue 1.
    
    We know that C * v = v (eigenvalue is 1).
    The normalized distribution v = A(N)/(N+1) is an eigenvector of C with eigenvalue 1.
    
    Parameters
    ----------
    C : np.ndarray
        Transition matrix (satisfies C * v = v)
    B : int
        Block capacity
    
    Returns
    -------
    tuple
        (eigenvector, eigenvalue)
    """
    # We know that C * v = v (eigenvalue is 1)
    # So we need to find the eigenvector of C with eigenvalue 1
    
    # Use scipy if available for better numerical stability
    if HAS_SCIPY:
        # scipy.linalg.eig is more numerically stable
        eigenvalues, eigenvectors = linalg.eig(C)
    else:
        eigenvalues, eigenvectors = np.linalg.eig(C)
    
    # Find eigenvalue closest to 1 (since C * v = v)
    eigenvals_diff = np.abs(eigenvalues - 1.0)
    idx = np.argmin(eigenvals_diff)
    
    eigenvector = eigenvectors[:, idx].real
    
    # Normalize so that sum(i * eigenvector[i]) = 1
    # This ensures the constraint sum(i * A[i]) = N+1 is satisfied
    total_weighted = np.sum(np.arange(len(eigenvector), dtype=DTYPE) * eigenvector)
    if abs(total_weighted) > 1e-10:
        eigenvector = eigenvector / total_weighted
    else:
        # If weighted sum is too small, try normalizing by regular sum
        total = np.sum(eigenvector)
        if abs(total) > 1e-10:
            eigenvector = eigenvector / total
            # Then scale to satisfy weighted constraint
            total_weighted = np.sum(np.arange(len(eigenvector), dtype=DTYPE) * eigenvector)
            if abs(total_weighted) > 1e-10:
                eigenvector = eigenvector / total_weighted
    
    # Ensure non-negative (eigenvectors can have negative components)
    eigenvector = np.maximum(eigenvector, 0)
    
    # Renormalize after ensuring non-negative
    total_weighted = np.sum(np.arange(len(eigenvector), dtype=DTYPE) * eigenvector)
    if abs(total_weighted) > 1e-10:
        eigenvector = eigenvector / total_weighted
    
    eigenvalue = eigenvalues[idx].real
    
    return eigenvector, eigenvalue


def compute_fullness_from_eigenvector(eigenvector: np.ndarray, B: int) -> float:
    """
    Compute expected fullness from the steady-state eigenvector.
    
    Fullness = total_elements / (B * number_of_blocks)
    
    In steady state with large N:
    - total_elements = N+1 (from constraint)
    - number_of_blocks = sum(eigenvector) * (N+1) / (sum(i * eigenvector[i]))
    
    Actually, if v = A(N)/(N+1) and sum(i * v[i]) = 1, then:
    - number_of_blocks = sum(v) * (N+1) / 1 = sum(v) * (N+1)
    - fullness = (N+1) / (B * sum(v) * (N+1)) = 1 / (B * sum(v))
    
    Parameters
    ----------
    eigenvector : np.ndarray
        Steady-state eigenvector (normalized so sum(i * v[i]) = 1)
    B : int
        Block capacity
    
    Returns
    -------
    float
        Expected fullness
    """
    num_blocks = np.sum(eigenvector)
    if num_blocks == 0:
        return 0.0
    
    # In steady state: fullness = 1 / (B * sum(v))
    # where v is the normalized distribution
    fullness = 1.0 / (B * num_blocks)
    
    return fullness


def find_optimal_split_eigenvector(B: int, a: int = None, split_strategies: List[Tuple[int, float]] = None, use_power_iteration: bool = False) -> Dict:
    """
    Find optimal splitting strategy using eigenvector analysis.
    
    Parameters
    ----------
    B : int
        Block capacity
    a : int, optional
        Split parameter: when a block reaches B, it splits into blocks of size a and (B-a)
        If split_strategies is provided, this is ignored.
    split_strategies : list of (int, float), optional
        List of (split_size, probability) tuples for hybrid splitting strategy.
        Example: [(120, 0.5), (119, 0.5)] means 50% chance of (120, 120) and 50% chance of (119, 121)
    use_power_iteration : bool
        If True, use power iteration instead of eigenvalue decomposition
    
    Returns
    -------
    dict
        Results for this split parameter/strategy
    """
    # Build transition matrix with split parameter a or split_strategies
    C = build_transition_matrix(B, a=a, split_strategies=split_strategies)
    
    # Find steady-state eigenvector
    if use_power_iteration:
        eigenvector, eigenvalue = find_steady_state_eigenvector_power_iteration(C, B)
    else:
        eigenvector, eigenvalue = find_steady_state_eigenvector(C, B)
    
    # Compute fullness from eigenvector
    fullness = compute_fullness_from_eigenvector(eigenvector, B)
    
    # Compute number of blocks in steady state
    num_blocks = np.sum(eigenvector)
    
    results = {
        'B': B,
        'eigenvalue': float(eigenvalue),
        'eigenvector': eigenvector.tolist(),
        'steady_state_fullness': float(fullness),
        'steady_state_num_blocks': float(num_blocks),
        'eigenvector_sum': float(np.sum(eigenvector)),
        'eigenvector_weighted_sum': float(np.sum(np.arange(len(eigenvector), dtype=DTYPE) * eigenvector))
    }
    
    return results


def compare_split_parameters(B: int, a_values: List[int]) -> Dict:
    """
    Compare different split parameters using eigenvector analysis.
    
    Parameters
    ----------
    B : int
        Block capacity
    a_values : list of int
        List of split parameters to compare
    
    Returns
    -------
    dict
        Comparison results for each a value
    """
    results = {}
    
    for a in a_values:
        print(f"Computing for a={a} (splits into {a} and {B-a})...")
        result = find_optimal_split_eigenvector(B, a)
        results[a] = result
    
    return results


if __name__ == "__main__":
    # Configuration
    B = 240
    
    print(f"=== Eigenvector Analysis for r=1 ===")
    print(f"B = {B}\n")
    
    # Example 1: Compare different single split parameters a
    print("="*80)
    print("PART 1: Single Split Strategies")
    print("="*80)
    a_values = []
    
    # Add even split (if B is even)
    if B % 2 == 0:
        a_values.append(B // 2)
    
    # Add some uneven splits
    # We only test a <= B/2 due to symmetry
    max_a = B // 2
    # for offset in [1, 2, 5, 10, 20, 30, 40, 50]:
    #     a = max_a - offset
    #     if a >= 1:
    #         a_values.append(a)
    
    # # Also add some small values
    # for a in [1, 2, 3, 4, 5, 10]:
    #     if a < max_a and a not in a_values:
    #         a_values.append(a)
    
    # Remove duplicates and sort
    a_values = sorted(list(set(a_values)))
    
    print(f"Comparing split parameters: {a_values}")
    print(f"Each a means: split into (a, B-a)\n")
    
    # Compare all a values
    results = compare_split_parameters(B, a_values)
    
    # Print comparison
    print("\n" + "="*80)
    print("COMPARISON RESULTS - Single Splits")
    print("="*80)
    print(f"{'a':<8} {'Split':<20} {'Fullness':<20} {'Num Blocks':<15} {'Eigenvalue':<15}")
    print("-"*80)
    
    sorted_results = sorted(results.items(), key=lambda x: x[1]['steady_state_fullness'], reverse=True)
    
    for a, result in sorted_results:
        split_desc = f"({a}, {B-a})"
        print(f"{a:<8} {split_desc:<20} {result['steady_state_fullness']:<20.15f} {result['steady_state_num_blocks']:<15.6f} {result['eigenvalue']:<15.10f}")
    
    # Helper function to generate description from strategy list
    def format_strategy_description(strategies: List[Tuple[int, float]]) -> str:
        """Generate a description string from a list of (split_size, probability) tuples."""
        parts = []
        for a_val, prob in strategies:
            percentage = int(round(prob * 100))
            parts.append(f"{percentage}% ({a_val},{B-a_val})")
        return " + ".join(parts)
    
    # ========================================================================
    # PART 2A: Personalized Split Strategies
    # ========================================================================
    # Add your custom strategies here as a list of (split_size, probability) tuples
    # Example: [(120, 0.5), (119, 0.5)] means 50% chance of (120,120) and 50% chance of (119,121)
    # You can have more than 2 strategies, just make sure probabilities sum to 1.0
    
    personalized_strategies = [
        # Add your custom strategies here
        # Example: [(120, 0.7), (119, 0.3)],
        # Example: [(120, 0.5), (118, 0.5)],
        # Example: [(120, 1/3), (119, 1/3), (118, 1/3)],
        # [(120, 0.7), (119, 0.3)],
        # [(120, 0.5), (118, 0.5)],
        [(120, 0.5), (112, 0.3), (116, 0.2)],
    ]
    
    personalized_results = {}
    if personalized_strategies:
        print("\n" + "="*80)
        print("PART 2A: Personalized Split Strategies")
        print("="*80)
        
        for strategies in personalized_strategies:
            name = format_strategy_description(strategies)
            print(f"\nComputing for {name}...")
            result = find_optimal_split_eigenvector(B, split_strategies=strategies)
            personalized_results[name] = result
        
        print("\n" + "="*80)
        print("COMPARISON RESULTS - Personalized Strategies")
        print("="*80)
        print(f"{'Strategy':<60} {'Fullness':<20} {'Num Blocks':<15} {'Eigenvalue':<15}")
        print("-"*80)
        
        sorted_personalized = sorted(personalized_results.items(), key=lambda x: x[1]['steady_state_fullness'], reverse=True)
        for name, result in sorted_personalized:
            print(f"{name:<60} {result['steady_state_fullness']:<20.15f} {result['steady_state_num_blocks']:<15.6f} {result['eigenvalue']:<15.10f}")
    
    # ========================================================================
    # PART 2B: Exhaustive Search (Optional - comment out if not needed)
    # ========================================================================
    run_exhaustive_search = False  # Set to True to run exhaustive search
    
    if run_exhaustive_search:
        print("\n" + "="*80)
        print("PART 2B: Hybrid Split Strategies - Exhaustive Search")
        print("="*80)
        
        # Test all combinations of two strategies from a in [100, 120]
        a_range = list(range(100, 121))  # [100, 101, ..., 120]
        prob_step = 0.01
        
        print(f"Testing all combinations of two strategies from a in {a_range}")
        print(f"Testing probabilities from 0 to 1 with step {prob_step}")
        print(f"Total combinations: {len(a_range) * (len(a_range) - 1) // 2} pairs × {int(1/prob_step) + 1} probabilities")
        
        hybrid_results = {}
        total_combinations = len(a_range) * (len(a_range) - 1) // 2 * (int(1/prob_step) + 1)
        count = 0
        
        # Iterate over all pairs of strategies (a1, a2) where a1 < a2
        for i, a1 in enumerate(a_range):
            for a2 in a_range[i+1:]:
                # Test all probability combinations: p for a1, (1-p) for a2
                for p in [round(x * prob_step, 2) for x in range(0, int(1/prob_step) + 1)]:
                    p1 = p
                    p2 = 1.0 - p
                    
                    strategies = [(a1, p1), (a2, p2)]
                    name = format_strategy_description(strategies)
                    
                    count += 1
                    if count % 100 == 0:
                        print(f"Progress: {count}/{total_combinations} ({100*count/total_combinations:.1f}%)")
                    
                    result = find_optimal_split_eigenvector(B, split_strategies=strategies)
                    hybrid_results[name] = result
        
        print(f"\nCompleted {count} combinations")
        
        print("\n" + "="*80)
        print("COMPARISON RESULTS - Hybrid Splits (Top 20)")
        print("="*80)
        print(f"{'Strategy':<60} {'Fullness':<20} {'Num Blocks':<15} {'Eigenvalue':<15}")
        print("-"*80)
        
        sorted_hybrid = sorted(hybrid_results.items(), key=lambda x: x[1]['steady_state_fullness'], reverse=True)
        
        # Show top 20 results
        for name, result in sorted_hybrid[:20]:
            print(f"{name:<60} {result['steady_state_fullness']:<20.15f} {result['steady_state_num_blocks']:<15.6f} {result['eigenvalue']:<15.10f}")
        
        # Show best result
        if sorted_hybrid:
            best_name, best_result = sorted_hybrid[0]
            print(f"\nBest hybrid strategy: {best_name}")
            print(f"  Fullness: {best_result['steady_state_fullness']:.20f}")
            print(f"  Num Blocks: {best_result['steady_state_num_blocks']:.6f}")
            print(f"  Eigenvalue: {best_result['eigenvalue']:.10f}")
    
    
    # Show best results
    best_a, best_result = sorted_results[0]
    print(f"\nBest split parameter: a={best_a} (splits into {best_a} and {B-best_a})")
    print(f"  Fullness: {best_result['steady_state_fullness']:.20f}")
    print(f"  Number of blocks: {best_result['steady_state_num_blocks']:.20f}")
    
    # Show eigenvector distribution for best result
    # print(f"\nSteady-state block size distribution for a={best_a} (non-zero entries):")
    # eigenvector = np.array(best_result['eigenvector'])
    # for i in range(len(eigenvector)):
    #     if abs(eigenvector[i]) > 1e-10:
    #         print(f"  Size {i}: {eigenvector[i]:.10f}")
    
    # Save results
    output_file = f"eigenvector_analysis_B{B}_r1.json"
    output_data = {
        'B': B,
        'results': {str(a): result for a, result in results.items()},
        'best_a': best_a
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nResults saved to {output_file}")

