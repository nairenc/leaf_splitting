# Hypothesis Test: Does the 5/9 Lower Bound Hold for Variable r?

## Background

**Known Result (Fixed r):**  
For immediately split with p=0.6 and any **fixed** batch size r, the time-averaged fullness satisfies:

```
fullness ≥ 5/9 ≈ 0.5556
```

## Research Question

**Does this guarantee still hold when using a variable batch size sequence instead of fixed r?**

## Test Design

### Sequence
We cycle through: **r ∈ {48, 96, 144, 192, 240}**

Corresponding to: **α ∈ {0.2, 0.4, 0.6, 0.8, 1.0}**

### Why This Sequence is Challenging

1. **Includes α=1.0** (worst case for immediately split: ~0.57 fullness)
2. **High variance** in workload intensity (0.2 to 1.0)
3. **No steady state** - constantly switching between regimes
4. **Mean α = 0.6** - moderate-heavy average workload

### Parameters
- B = 240
- p = 0.6 (the ratio with known 5/9 guarantee)
- Repetitions = 1,000,000 (ensures steady state despite variability)
- Seeds = 20 (statistical confidence)

## Possible Outcomes

### Outcome A: fullness ≥ 5/9 + ε (e.g., ≥ 0.58)

**Interpretation:** ✅ Lower bound extends to variable r  
**Conclusion:** The 5/9 guarantee is robust and holds even with time-varying workloads  
**Implication:** Theory is stronger than expected

### Outcome B: fullness ≈ 5/9 (e.g., 0.556 ± 0.01)

**Interpretation:** ⚠️ This sequence achieves the lower bound  
**Conclusion:** We found an "adversarial" sequence that matches the worst case  
**Implication:** The bound is tight, and variable r can be as bad as the worst fixed r

### Outcome C: fullness < 5/9 (e.g., < 0.55)

**Interpretation:** ❌ Lower bound does NOT extend to variable r  
**Conclusion:** Variable workloads can break the guarantee  
**Implication:** Need new theoretical analysis for time-varying batch sizes  
**Significance:** Major finding! Would require revisiting the theory

## Predictions

### Conservative Estimate
Based on α=1.0 bottleneck (~0.57) dominating:

```
Expected fullness: 0.58 - 0.60
```

### Optimistic Estimate
Based on weighted average of fixed r results:

```
Expected fullness: 0.61 - 0.63
```

### Worst Case
If transient effects are highly unfavorable:

```
Worst case fullness: 0.56 - 0.58
```

**Most likely:** Result will be **above 5/9** but **below** the average of fixed r values due to α=1.0 influence.

## Key Metrics to Check

1. **time_avg_fullness_mean** - Main metric of interest
2. Compare to **5/9 = 0.555556**
3. Compare to fixed r results at p=0.6 for r ∈ {48, 96, 144, 192, 240}

## Interpretation Guide

| Result Range | Meaning |
|--------------|---------|
| ≥ 0.63 | Theory extends cleanly, weighted average behavior |
| 0.60 - 0.63 | Some penalty from mixing, but above 5/9 |
| 0.56 - 0.60 | Close to or at the bound |
| < 0.56 | **Breaking the bound!** Major finding |

## Follow-up Questions

If fullness < 5/9:
- Which other sequences break the bound?
- Is there a pattern to adversarial sequences?
- Can we characterize the worst-case sequence?

If fullness ≈ 5/9:
- Is this the worst possible sequence?
- What makes this sequence special?
- Can we prove it's optimal?

If fullness > 5/9:
- Can we prove a bound for variable r?
- Is the bound still 5/9 or something else?
- How does the bound depend on sequence properties?

## Timeline

1. **Submit job** → Run 20 tasks (2-4 hours each)
2. **Collect results** → Aggregate across seeds
3. **Compare to 5/9** → Check hypothesis
4. **Analyze** → Understand the result
5. **Follow-up** → Design additional tests if needed

---

**This is a hypothesis-testing experiment!** The result will guide future theoretical and experimental work.

