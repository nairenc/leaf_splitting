from collections import defaultdict

# ---------------------------------------------------------
# Core dynamics (float + pruning)
# ---------------------------------------------------------

def step_distribution_float(dist, B, eps=1e-20, renormalize=True):
    """
    One insertion step, using float probabilities.

    dist: dict mapping state -> probability (float).
          state is a sorted tuple of block sizes, e.g. (4,4) or (3,5,6).
    B:    block capacity.
    eps:  prune states whose probability (after renormalization) is below eps.
    renormalize: if True, re-scale probabilities to sum to 1 after pruning.

    Returns a new dict for the distribution after one insertion.
    """
    new_dist = defaultdict(float)

    for state, p_state in dist.items():
        if p_state == 0.0:
            continue
        total = float(sum(state))  # total number of elements currently

        for i, s in enumerate(state):
            prob_hit = float(s) / total

            if s + 1 == B:
                # This block grows to B and then splits into two blocks
                # For even B: split into (B/2, B/2)
                # For odd B: split into (B//2, B//2+1) to preserve total elements
                split_left = B // 2
                split_right = B - split_left  # Ensures split_left + split_right == B
                new_state_list = list(state[:i] + state[i+1:]) + [split_left, split_right]
            else:
                # Just increment this block by 1
                new_state_list = list(state)
                new_state_list[i] += 1

            new_state_list.sort()
            new_state = tuple(new_state_list)
            new_dist[new_state] += p_state * prob_hit

    # Optionally renormalize and prune tiny states
    total_prob = sum(new_dist.values())
    if total_prob == 0.0:
        return {}

    if renormalize:
        inv_total = 1.0 / total_prob
        new_dist = {s: p * inv_total for s, p in new_dist.items()}
    else:
        # keep as-is; eps is interpreted on unnormalized probs
        pass

    if eps is not None and eps > 0.0:
        new_dist = {s: p for s, p in new_dist.items() if p >= eps}

        # Optionally renormalize again after pruning
        if renormalize:
            total_prob = sum(new_dist.values())
            if total_prob > 0.0:
                inv_total = 1.0 / total_prob
                new_dist = {s: p * inv_total for s, p in new_dist.items()}

    return new_dist


def run_process_float(B, init_state, steps, eps=1e-20, max_states=500000):
    """
    Run the process for a fixed number of insertion steps, using floats.

    B:          block capacity.
    init_state: iterable of initial block sizes, e.g. (4,4) or (3,5).
    steps:      number of elements to insert.
    eps:        pruning threshold.
    max_states: safety cap on number of states.

    Returns a dict mapping state -> probability (float).
    """
    state0 = tuple(sorted(init_state))
    dist = {state0: 1.0}

    for _ in range(steps):
        dist = step_distribution_float(dist, B, eps=eps, renormalize=True)
        if len(dist) > max_states:
            raise RuntimeError(f"State space exploded beyond {max_states} states")
    return dist


def expected_fullness_float(B, init_state, steps, eps=1e-20, return_dist=False, max_states=200000):
    """
    Compute expected fullness after 'steps' insertions using floats.

    Fullness = total_elements / (B * #blocks).
    total_elements = sum(init_state) + steps.
    """
    dist = run_process_float(B, init_state, steps, eps=eps, max_states=max_states)
    total_elements = sum(init_state) + steps

    exp_full = 0.0
    for state, p in dist.items():
        k = len(state)  # number of blocks
        fullness = float(total_elements) / (B * k)
        exp_full += p * fullness

    if return_dist:
        return exp_full, dist
    else:
        return exp_full


# ---------------------------------------------------------
# Range comparison using incremental evolution (float)
# ---------------------------------------------------------

def compare_range_incremental_float(B, init1, init2, max_steps, eps=1e-20, max_states=500000):
    """
    Compare expected fullness of two initial states over steps = 0..max_steps
    using a single forward pass (reusing intermediate distributions), floats.

    B:         block capacity
    init1:     initial state for case 1, e.g. (4,4)
    init2:     initial state for case 2, e.g. (3,5)
    max_steps: max number of insertions to simulate
    eps:       pruning threshold
    """
    state1 = {tuple(sorted(init1)): 1.0}
    state2 = {tuple(sorted(init2)): 1.0}

    base1 = sum(init1)
    base2 = sum(init2)

    results = []
    better1 = better2 = equal = 0

    for steps in range(max_steps + 1):
        if len(state1) > max_states or len(state2) > max_states:
            raise RuntimeError(f"State space exploded beyond {max_states} states at step {steps}")

        total1 = base1 + steps
        total2 = base2 + steps

        # expected fullness from current distributions
        exp1 = 0.0
        for s, p in state1.items():
            k = len(s)
            fullness = float(total1) / (B * k)
            exp1 += p * fullness

        exp2 = 0.0
        for s, p in state2.items():
            k = len(s)
            fullness = float(total2) / (B * k)
            exp2 += p * fullness

        if exp1 > exp2:
            relation = "case1>case2"
            better1 += 1
        elif exp1 < exp2:
            relation = "case1<case2"
            better2 += 1
        else:
            relation = "equal"
            equal += 1

        results.append((steps, exp1, exp2, relation))

        # advance one step for the next iteration
        if steps < max_steps:
            state1 = step_distribution_float(state1, B, eps=eps, renormalize=True)
            state2 = step_distribution_float(state2, B, eps=eps, renormalize=True)

    return results, better1, better2, equal


# ---------------------------------------------------------
# Helper: inspect a single step (float)
# ---------------------------------------------------------

def print_single_step_float(B, init_state, steps, eps=1e-20, max_states=500000):
    """
    Print the distribution and expected fullness after 'steps' insertions
    from 'init_state' using floats.
    """
    exp_full, dist = expected_fullness_float(
        B, init_state, steps, eps=eps, return_dist=True, max_states=max_states
    )
    total_elements = sum(init_state) + steps

    print(f"B = {B}, init_state = {tuple(sorted(init_state))}, steps = {steps}")
    print(f"total elements = {total_elements}")
    print(f"expected fullness ≈ {exp_full:.12f}\n")
    print("Final state distribution (state, prob, #blocks, fullness):")
    # for state, p in sorted(dist.items()):
    #     k = len(state)
    #     fullness = float(total_elements) / (B * k)
    #     print(
    #         f"  state={state}, "
    #         f"prob≈{p:.12e}, "
    #         f"#blocks={k}, fullness≈{fullness:.6f}"
    #     )
    # print()


# ---------------------------------------------------------
# Example usage
# ---------------------------------------------------------

if __name__ == "__main__":
    B = 26
    case1 = (13, 13)   # even split
    case2 = (11, 15)   # uneven split
    eps = 1e-20      # "20th fractional" precision-ish
    max_steps = 200

    # 1) Check one specific step
    steps_to_check = B + 1
    print_single_step_float(B, case1, steps_to_check, eps=eps)
    print_single_step_float(B, case2, steps_to_check, eps=eps)

    # 2) Compare a whole range of steps
    results, better1, better2, equal = compare_range_incremental_float(
        B, case1, case2, max_steps, eps=eps
    )

    print(f"Range comparison for B={B}, steps 0..{max_steps}")
    print("case1 init:", case1, "case2 init:", case2)
    print("case1>case2 steps:", better1)
    print("case1<case2 steps:", better2)
    print("equal steps:", equal)
    print()

    # for steps, f1, f2, rel in results:
    #     print(
    #         f"steps={steps:2d}: "
    #         f"full1≈{f1:.8f}, "
    #         f"full2≈{f2:.8f}, {rel}"
    #     )
