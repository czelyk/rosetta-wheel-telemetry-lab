from bisect import bisect_left
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import median

WHEELS = dict(zip("ABCD", zip(
    ("nacw0g05", "nacw0g0h", "nacw0g0t", "nacw0g15"),
    ("nacg0010", "nacg0011", "nacg0012", "nacg0013"),
)))
QUARTERS = ("2014_q4", "2015_q3", "2016_q2")
START = datetime(2000, 1, 1)

def read(quarter, key):
    source = Path("data", quarter, f"ros_hk_{key}_{quarter}.tab")
    rows = []
    for line in source.read_text(encoding="ascii").splitlines():
        when, value = line.split(",")
        t = round((datetime.fromisoformat(when) - START).total_seconds() * 1000)
        rows.append((t, float(value)))
    assert all(a[0] < b[0] for a, b in zip(rows, rows[1:])), source
    return rows

def analyze(quarter, wheel, torque_key, momentum_key):
    torque = read(quarter, torque_key)
    momentum = read(quarter, momentum_key)
    momentum_times = [t for t, _ in momentum]
    all_deltas = []
    over_limit = []
    exact = 0
    for t, v in torque:
        i = bisect_left(momentum_times, t)
        neighbors = momentum[max(0, i - 1):i + 1]
        nearest, nearest_value = min(neighbors, key=lambda row: abs(row[0] - t))
        delta = nearest - t
        exact += delta == 0
        all_deltas.append(delta)
        if abs(v) >= .05:
            over_limit.append((t, v, delta, nearest_value))
    top_deltas = Counter(round(d / 1000, 1) for d in all_deltas).most_common(6)
    gaps = [b[0] - a[0] for a, b in zip(torque, torque[1:])]
    print(quarter, wheel, "torque_n", len(torque), "momentum_n", len(momentum),
          "cadence_sec", round(median(gaps)/1000, 3),
          "gaps_le_1s", sum(d <= 1000 for d in gaps),
          "exact_pairs", exact, "nearest_le_1s", sum(abs(d) <= 1000 for d in all_deltas),
          "modal_nearest_sec", top_deltas,
          "max_mNm", round(max(abs(v) for _, v in torque) * 1000, 3),
          "threshold_counts", {n: sum(abs(v) * 1000 >= n for _, v in torque)
                               for n in (20, 30, 40, 50)})
    return over_limit

if __name__ == "__main__":
    for quarter in QUARTERS:
        for wheel, (torque, momentum) in WHEELS.items():
            analyze(quarter, wheel, torque, momentum)
