import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.leaf_splitting_sim import simulate_variable_r


B = 240
p = 0.6
method = 'immediately'

# schedule:
#   - first: repeat [6, 7, 8] 10,000 times
#   - then:  repeat [20]       5,000 times
r_schedule = [
    [200000, 144, 96, ],
    [200000, 40],
]

res = simulate_variable_r(
    B=B,
    r_seq=r_schedule,   # compressed spec
    method=method,
    p=p,
    seed=2378,
    track_fullness_curve=True,
)

print("final fullness:", res["final_fullness"])
print("time-avg fullness:", res["time_avg_fullness"])

curve = res["fullness_curve"]

# x-axis = "batch index" (each batch is one r in the sequence)
steps = np.arange(1, len(curve) + 1)

plt.figure()
plt.plot(steps, curve)
plt.xlabel("Batch index")
plt.ylabel("Instantaneous fullness  n / (B * #blocks)")
plt.title(f"Fullness curve, B={B}, method={method}, p={p}")
plt.tight_layout()
plt.show()