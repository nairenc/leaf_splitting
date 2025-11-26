# Quick Start - Hard Case Test (p=0.6, Variable r)

## 🎯 Purpose

Test if the **5/9 lower bound** for p=0.6 holds when using a **variable batch size sequence**.

## 📊 Configuration

```
B = 240
p = 0.6
r_sequence = [48, 96, 144, 192, 240]  ← α ∈ {0.2, 0.4, 0.6, 0.8, 1.0}
Repetitions = 1,000,000
Seeds = 20
Total insertions per task = 720 million
```

## 🔬 Preliminary Result (1 seed)

**Time-avg fullness: 0.5678**

This is only **2.2% above** the 5/9 = 0.5556 theoretical bound!

**Interpretation:** This sequence is near-adversarial but still respects the bound.

## 🚀 To Submit

```bash
cd runs/B240_immediately_hardcase_p06_seq1M
sbatch submit_slurm.sh
```

Expected time: 2-4 hours per task (20 tasks running in parallel)

## 📥 After Completion

```bash
# Collect results
python ../../leaf_splitting_sim_sequence_slurm.py collect \
    --results_dir results \
    --output B240_immediately_hardcase_p06_aggregated.csv

# Check the result
python3 << EOF
import pandas as pd
df = pd.read_csv('B240_immediately_hardcase_p06_aggregated.csv')
fullness = df['time_avg_fullness_mean'].values[0]
std = df['time_avg_fullness_std'].values[0]
bound = 5/9

print(f"\\n{'='*60}")
print(f"RESULT: Time-avg fullness = {fullness:.6f} ± {std:.6f}")
print(f"BOUND:  5/9 = {bound:.6f}")
print(f"MARGIN: {fullness - bound:.6f} ({(fullness/bound - 1)*100:.2f}% above bound)")
print(f"{'='*60}\\n")

if fullness > bound + 0.01:
    print("✅ Bound clearly holds for variable r")
elif fullness > bound:
    print("⚠️  Bound holds but sequence is near-adversarial")
else:
    print("❌ BOUND VIOLATED! Major finding!")
EOF
```

## 📚 Documentation

- **HYPOTHESIS.md** - Research question and predictions
- **TEST_RESULT.md** - Preliminary test analysis  
- **README.md** - Full documentation

## 🎲 Expected Result

Based on preliminary test:

**Mean fullness: 0.565 - 0.570**  
**Status: Above 5/9 but close to the bound**

This would confirm:
- ✅ Theory extends to variable r
- ⚠️ But this sequence is near-worst-case
- 📉 Significant penalty from mixing workloads

---

**Ready to submit!** This is a hypothesis-testing experiment. 🧪

