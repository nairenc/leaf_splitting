import numpy as np
from typing import Tuple, List

# Set numpy to use higher precision and display more digits
np.seterr(all='warn')  # Warn on precision issues
# Use float128 for higher precision (if available, otherwise float64)
# Note: float128 may not be true 128-bit on all platforms, but provides extended precision
DTYPE = np.float128 if hasattr(np, 'float128') else np.float64

# ---------------------------------------------------------
# Matrix-based expectation computation
# ---------------------------------------------------------

def build_transition_matrix(B: int) -> np.ndarray:
    """
    Build the transition matrix C for the block size distribution.
    
    Assumes B is even for simplicity.
    
    A(N) is a vector where A[i] = number of blocks of size i.
    When we insert an element:
    - We pick a block of size i with probability i/total
    - If i+1 < B: block becomes size i+1
    - If i+1 == B: block splits into two blocks of size B/2
    
    In matrix C:
    - C[i, j] = change in blocks of size i when we hit a block of size j
    - C[j, j] = -j (blocks of size j decrease, weighted by probability j/total)
    - C[j+1, j] = j (blocks of size j+1 increase, weighted by probability j/total)
    - Special case: C[B/2, B-1] = 2*(B-1) and C[B-1, B-1] = -(B-1) (split case)
    
    The user's notation C[i-1, i] = i-1 means: when we hit size (i-1), blocks of size i increase.
    This is equivalent to C[i, i-1] = i-1 in our row/column interpretation.
    
    Note: The matrix satisfies sum(j * C[j, i]) = i for each column i.
    This means when we compute C @ A, the weighted sum is preserved.
    However, for the evolution A(N+1) = (I*N/(N+1) + C/(N+1)) @ A(N) to work correctly,
    we need to ensure the total elements increase by 1. The current implementation
    may need adjustment to account for this.
    
    Parameters
    ----------
    B : int
        Block capacity (assumed to be even)
    
    Returns
    -------
    np.ndarray
        Transition matrix of shape (B+1, B+1)
    """
    # Matrix indices: 0 to B (inclusive)
    # C[i, j] represents the change in blocks of size i when we hit a block of size j
    # Row i = blocks of size i, Column j = what happens when we hit size j
    # 
    # For blocks of size i:
    # - Increases when we hit size (i-1): C[i, i-1] = i-1
    # - Decreases when we hit size i: C[i, i] = -i
    C = np.zeros((B + 1, B + 1), dtype=DTYPE)
    
    for i in range(1, B + 1):
        if i < B:
            # Normal case: blocks of size i
            # Decrease when we hit size i
            C[i, i] = -i  # decrease in blocks of size i (weighted by probability i/total)
            # Increase when we hit size (i-1)
            if i - 1 >= 1:
                C[i, i - 1] = i - 1  # increase in blocks of size i (weighted by probability (i-1)/total)
        elif i == B:
            # Blocks of size B don't exist (they split immediately), but we handle it for completeness
            pass
    
    # Special case: when we hit size B-1, it splits into two blocks of size B/2
    # So blocks of size B/2 increase when we hit size B-1
    split_size = B // 2
    C[split_size, B - 1] = 2 * (B - 1)  # increase in blocks of size B/2 (two blocks created)
    
    return C


def initial_state_to_vector(init_state: Tuple[int, ...], B: int) -> np.ndarray:
    """
    Convert initial state (tuple of block sizes) to vector A(0).
    
    Parameters
    ----------
    init_state : tuple
        Initial block sizes, e.g. (13, 13) or (11, 15)
    B : int
        Block capacity (determines vector size)
    
    Returns
    -------
    np.ndarray
        Vector A where A[i] = number of blocks of size i
    """
    A = np.zeros(B + 1, dtype=DTYPE)
    for size in init_state:
        if 0 <= size <= B:
            A[size] += 1
    return A


def compute_fullness(A: np.ndarray, total_elements: int, B: int) -> float:
    """
    Compute expected fullness from block size distribution vector A.
    
    Fullness = total_elements / (B * number_of_blocks)
    
    Parameters
    ----------
    A : np.ndarray
        Block size distribution vector
    total_elements : int
        Total number of elements
    B : int
        Block capacity
    
    Returns
    -------
    float
        Expected fullness
    """
    num_blocks = np.sum(A)
    if num_blocks == 0:
        return 0.0
    return total_elements / (B * num_blocks)


def evolve_distribution(A: np.ndarray, C: np.ndarray, N: int) -> np.ndarray:
    """
    Compute A(N+1) from A(N) using the transition matrix.
    
    A(N+1) = (I + C/N) * A(N)
    
    The C/N term applies transitions weighted by probabilities.
    The matrix C satisfies: sum(j * C[j, i]) = i for each column i.
    
    Parameters
    ----------
    A : np.ndarray
        Current distribution A(N), where sum(i*A[i]) = N
    C : np.ndarray
        Transition matrix where sum(j*C[j,i]) = i
    N : int
        Current number of elements (should equal sum(i*A[i]))
    
    Returns
    -------
    np.ndarray
        Next distribution A(N+1), where sum(i*A[i]) = N+1
    """
    # Verify that N equals the total number of elements
    total_from_A = np.sum(np.arange(len(A), dtype=DTYPE) * A)
    # Use a tolerance based on the data type's epsilon and the magnitude of N
    eps = np.finfo(DTYPE).eps
    tolerance = max(eps * abs(N), 1e-10)
    if abs(total_from_A - N) > tolerance:
        # import warnings
        # warnings.warn(
        #     f"N ({N}) does not match total elements from A ({total_from_A:.20f}). "
        #     f"Difference: {abs(total_from_A - N):.20e}. "
        #     f"Using actual total from A.",
        #     RuntimeWarning
        # )
        # Use the actual total from A instead of N for consistency
        N = total_from_A
    
    I = np.eye(len(A))
    # The evolution: A(N+1) = (I + C/N) * A(N)
    transition = I + C / N
    A_new = transition @ A
    
    return A_new


def compute_expectation_matrix(B: int, init_state: Tuple[int, ...], steps: int, 
                               return_time_avg: bool = False) -> Tuple[float, np.ndarray, float]:
    """
    Compute expected fullness after 'steps' insertions using matrix operations.
    
    Parameters
    ----------
    B : int
        Block capacity (assumed to be even)
    init_state : tuple
        Initial block sizes, e.g. (13, 13) or (11, 15)
    steps : int
        Number of elements to insert
    return_time_avg : bool
        If True, also compute and return time-averaged fullness
    
    Returns
    -------
    tuple
        (expected_fullness, final_distribution_vector, time_avg_fullness)
        If return_time_avg is False, time_avg_fullness will be 0.0
    """
    # Build transition matrix
    C = build_transition_matrix(B)
    
    # Initialize distribution vector
    A = initial_state_to_vector(init_state, B)
    
    # Initial number of elements
    N = sum(init_state)
    
    # For time-averaged fullness: sum(elements) / sum(B * blocks)
    elem_tally = 0.0
    capacity_tally = 0.0
    
    # Evolve for 'steps' iterations
    for _ in range(steps):
        if return_time_avg:
            # Accumulate for time-averaged fullness
            num_blocks = np.sum(A)
            elem_tally += N
            capacity_tally += B * num_blocks
        
        A = evolve_distribution(A, C, N)
        N += 1
    
    # Compute expected fullness
    total_elements = sum(init_state) + steps
    exp_fullness = compute_fullness(A, total_elements, B)
    
    # Compute time-averaged fullness
    time_avg_fullness = 0.0
    if return_time_avg:
        # Add final step
        num_blocks = np.sum(A)
        elem_tally += N
        capacity_tally += B * num_blocks
        
        if capacity_tally > 0:
            time_avg_fullness = elem_tally / capacity_tally
    
    return exp_fullness, A, time_avg_fullness


def compare_range_matrix(B: int, init1: Tuple[int, ...], init2: Tuple[int, ...], 
                         max_steps: int, include_time_avg: bool = True) -> Tuple[List, int, int, int, float, float, int, int, int]:
    """
    Compare expected fullness of two initial states over steps = 0..max_steps
    using matrix operations.
    
    Parameters
    ----------
    B : int
        Block capacity (assumed to be even)
    init1 : tuple
        Initial state for case 1, e.g. (13, 13)
    init2 : tuple
        Initial state for case 2, e.g. (11, 15)
    max_steps : int
        Max number of insertions to simulate
    
    Returns
    -------
    tuple
        (results_list, better1_count, better2_count, equal_count, 
         time_avg1, time_avg2, time_avg_better1, time_avg_better2, time_avg_equal)
        results_list contains (steps, fullness1, fullness2, relation) tuples
        time_avg_better1/2/equal: counts for time-averaged fullness comparisons
    """
    # Build transition matrix
    C = build_transition_matrix(B)
    
    # Initialize distribution vectors
    A1 = initial_state_to_vector(init1, B)
    A2 = initial_state_to_vector(init2, B)
    
    # Initial number of elements
    N1 = sum(init1)
    N2 = sum(init2)
    
    results = []
    better1 = better2 = equal = 0
    
    # For time-averaged fullness comparisons at each step
    time_avg_better1 = 0
    time_avg_better2 = 0
    time_avg_equal = 0
    
    # For time-averaged fullness: sum(elements) / sum(B * blocks)
    elem_tally1 = 0.0
    capacity_tally1 = 0.0
    elem_tally2 = 0.0
    capacity_tally2 = 0.0
    
    # Progress reporting for large max_steps
    progress_interval = max(1, max_steps // 100) if max_steps > 1000 else max_steps + 1
    
    for steps in range(max_steps + 1):
        if steps % progress_interval == 0 and max_steps > 1000:
            print(f"Progress: {steps}/{max_steps} ({100*steps/max_steps:.1f}%)", end='\r')
        
        # Compute current fullness
        total1 = N1
        total2 = N2
        
        fullness1 = compute_fullness(A1, total1, B)
        fullness2 = compute_fullness(A2, total2, B)
        
        # Accumulate for time-averaged fullness
        if include_time_avg:
            num_blocks1 = np.sum(A1)
            num_blocks2 = np.sum(A2)
            elem_tally1 += total1
            capacity_tally1 += B * num_blocks1
            elem_tally2 += total2
            capacity_tally2 += B * num_blocks2
            
            # Compute time-averaged fullness up to this step
            time_avg1 = elem_tally1 / capacity_tally1 if capacity_tally1 > 0 else 0.0
            time_avg2 = elem_tally2 / capacity_tally2 if capacity_tally2 > 0 else 0.0
            
            # Compare time-averaged fullness
            if time_avg1 > time_avg2:
                time_avg_better1 += 1
            elif time_avg1 < time_avg2:
                time_avg_better2 += 1
            else:
                time_avg_equal += 1
        
        if fullness1 > fullness2:
            relation = "case1>case2"
            better1 += 1
        elif fullness1 < fullness2:
            relation = "case1<case2"
            better2 += 1
        else:
            relation = "equal"
            equal += 1
        
        results.append((steps, fullness1, fullness2, relation))
        
        # Evolve for next iteration
        if steps < max_steps:
            A1 = evolve_distribution(A1, C, N1)
            A2 = evolve_distribution(A2, C, N2)
            N1 += 1
            N2 += 1
    
    # Compute final time-averaged fullness
    time_avg1 = elem_tally1 / capacity_tally1 if capacity_tally1 > 0 else 0.0
    time_avg2 = elem_tally2 / capacity_tally2 if capacity_tally2 > 0 else 0.0
    
    return results, better1, better2, equal, time_avg1, time_avg2, time_avg_better1, time_avg_better2, time_avg_equal


def print_single_step_matrix(B: int, init_state: Tuple[int, ...], steps: int):
    """
    Print the distribution and expected fullness after 'steps' insertions
    from 'init_state' using matrix operations.
    """
    exp_full, A, time_avg = compute_expectation_matrix(B, init_state, steps, return_time_avg=True)
    total_elements = sum(init_state) + steps
    
    # Verify element conservation: sum(i * A[i]) should equal total_elements
    total_from_dist = np.sum(np.arange(len(A)) * A)
    num_blocks = np.sum(A)
    
    print(f"B = {B}, init_state = {tuple(sorted(init_state))}, steps = {steps}")
    print(f"total elements = {total_elements}")
    print(f"total from distribution = {total_from_dist:.6f}")
    print(f"expected fullness ≈ {exp_full:.20f}")
    print(f"time-averaged fullness ≈ {time_avg:.20f}")
    print(f"number of blocks = {num_blocks:.6f}")
    print(f"average block size = {total_from_dist/num_blocks:.6f}" if num_blocks > 0 else "N/A")
    print()


# ---------------------------------------------------------
# Example usage
# ---------------------------------------------------------

if __name__ == "__main__":
    B = 480
    case1 = (B // 2, B - B // 2)   # even split
    case2 = (B // 2 - 10, B - B // 2 + 10)   # uneven split
    max_steps = 10*B
    
    # Debug: Check transition matrix structure
    print("=== Debug: Transition Matrix ===")
    C = build_transition_matrix(B)
    print(f"Matrix shape: {C.shape}")
    print(f"Non-zero entries (first 10 rows):")
    for i in range(min(10, B+1)):
        non_zero = [(j, C[i, j]) for j in range(B+1) if abs(C[i, j]) > 1e-10]
        if non_zero:
            print(f"  Row {i} (blocks of size {i}): {non_zero}")
    print()
    
    # 1) Check one specific step
    steps_to_check = B + 1
    print("=== Matrix-based computation ===")
    print_single_step_matrix(B, case1, steps_to_check)
    print_single_step_matrix(B, case2, steps_to_check)
    
    # 2) Compare a whole range of steps
    print("=== Range comparison ===")
    results, better1, better2, equal, time_avg1, time_avg2, time_avg_better1, time_avg_better2, time_avg_equal = compare_range_matrix(
        B, case1, case2, max_steps, include_time_avg=True
    )
    
    print(f"Range comparison for B={B}, steps 0..{max_steps}")
    print("case1 init:", case1, "(even split)")
    print("case2 init:", case2, "(uneven split)")
    print()
    print("--- Final Fullness Comparison ---")
    print("case1>case2 steps (even better):", better1)
    print("case1<case2 steps (uneven better):", better2)
    print("equal steps:", equal)
    print(f"Uneven split is better {100*better2/(better1+better2+equal):.2f}% of the time")
    print()
    print("--- Time-Averaged Fullness Comparison ---")
    print("case1>case2 steps (even better):", time_avg_better1)
    print("case1<case2 steps (uneven better):", time_avg_better2)
    print("equal steps:", time_avg_equal)
    total_time_avg = time_avg_better1 + time_avg_better2 + time_avg_equal
    if total_time_avg > 0:
        print(f"Uneven split has better time-avg fullness {100*time_avg_better2/total_time_avg:.2f}% of the time")
    print()
    print("--- Final Time-Averaged Fullness Values ---")
    print(f"  case1 (even):   {time_avg1:.20f}")
    print(f"  case2 (uneven): {time_avg2:.20f}")
    print(f"  Difference:     {time_avg2 - time_avg1:.20f} ({100*(time_avg2-time_avg1)/time_avg1:+.4f}%)")
    print()
    
    # Find when the advantage switches
    switch_points = []
    prev_rel = None
    for steps, f1, f2, rel in results:
        if prev_rel and rel != prev_rel:
            switch_points.append((steps, prev_rel, rel))
        prev_rel = rel
    
    if switch_points:
        print(f"Found {len(switch_points)} switch points:")
        for step, from_rel, to_rel in switch_points[:10]:  # Show first 10
            print(f"  Step {step}: {from_rel} -> {to_rel}")
        if len(switch_points) > 10:
            print(f"  ... and {len(switch_points)-10} more")
        print()
    
    # Print first and last few results
    # print("First 10 steps:")
    # for steps, f1, f2, rel in results[:10]:
    #     print(f"steps={steps:2d}: full1≈{f1:.20f}, full2≈{f2:.20f}, {rel}")
    
    if len(results) > 100:
        print("\nLast 10 steps:")
        for steps, f1, f2, rel in results[-100:]:
            print(f"steps={steps:2d}: full1≈{f1:.20f}, full2≈{f2:.20f}, {rel}")

