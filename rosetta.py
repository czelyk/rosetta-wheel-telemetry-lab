"""Read pinned Rosetta wheel telemetry and audit time alignment."""

import csv
import hashlib
import math
import re
from bisect import bisect_left
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "data" / "manifest.tsv"
EPOCH = datetime(2000, 1, 1)
QUARTERS = ("2014_q4", "2015_q3", "2016_q2")
WHEELS = (
    ("A", "nacw0g05", "nacg0010"),
    ("B", "nacw0g0h", "nacg0011"),
    ("C", "nacw0g0t", "nacg0012"),
    ("D", "nacw0g15", "nacg0013"),
)
TOLERANCE_MS = 20_000
INTERPOLATION_GAP_MS = 128_000


def read_manifest():
    entries = {}
    with MANIFEST.open(encoding="utf-8", newline="") as stream:
        for filename, size, digest, url in csv.reader(stream, delimiter="\t"):
            match = re.fullmatch(r"ros_hk_[a-z0-9]+_(\d{4}_q[1-4])\.(lbl|tab)", filename)
            if match is None or filename in entries:
                raise ValueError(f"Invalid or duplicate manifest filename: {filename}")
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError(f"Invalid SHA-256 for {filename}")
            entries[filename] = {
                "path": Path(match[1]) / filename,
                "size": int(size),
                "sha256": digest,
                "url": url,
            }
    expected = {
        f"ros_hk_{parameter}_{quarter}.{extension}"
        for quarter in QUARTERS
        for _, torque, momentum in WHEELS
        for parameter in (torque, momentum)
        for extension in ("lbl", "tab")
    }
    if entries.keys() != expected:
        raise ValueError("Manifest must contain the 48 declared PDS products")
    return entries


def verify_content(content, entry):
    if len(content) != entry["size"]:
        raise ValueError(f"Size mismatch for {entry['path']}")
    digest = hashlib.sha256(content).hexdigest()
    if digest != entry["sha256"]:
        raise ValueError(f"SHA-256 mismatch for {entry['path']}")


def verify_inputs(data_directory, entries):
    records = []
    for entry in entries.values():
        path = data_directory / entry["path"]
        verify_content(path.read_bytes(), entry)
        records.append({
            "path": entry["path"].as_posix(),
            "bytes": entry["size"],
            "sha256": entry["sha256"],
        })
    return records


def milliseconds(timestamp):
    elapsed = datetime.fromisoformat(timestamp) - EPOCH
    if elapsed.microseconds % 1000:
        raise ValueError(f"Timestamp exceeds archive millisecond resolution: {timestamp}")
    return (elapsed.days * 86400 + elapsed.seconds) * 1000 + elapsed.microseconds // 1000


def read_series(data_directory, quarter, parameter, expected_unit):
    stem = f"ros_hk_{parameter}_{quarter}"
    label = (data_directory / quarter / f"{stem}.lbl").read_text(encoding="ascii")
    declared_rows = re.search(r"^\s*ROWS\s*=\s*(\d+)\s*$", label, re.MULTILINE)
    units = re.findall(r'^\s*UNIT\s*=\s*"([^"]+)"\s*$', label, re.MULTILINE)
    if declared_rows is None or not units or units[-1] != expected_unit:
        raise ValueError(f"Unexpected PDS row count or units for {stem}")

    rows = []
    path = data_directory / quarter / f"{stem}.tab"
    with path.open(encoding="ascii", newline="") as stream:
        for line in stream:
            timestamp, raw_value = line.strip().split(",")
            tick, value = milliseconds(timestamp), float(raw_value)
            if not math.isfinite(value) or (rows and tick <= rows[-1][0]):
                raise ValueError(f"Non-finite value or unordered timestamp in {path.name}")
            rows.append((tick, value))
    if len(rows) != int(declared_rows[1]) or len(rows) < 2:
        raise ValueError(f"PDS row count mismatch for {stem}")
    return rows


def momentum_match(times, values, tick):
    """Keep prior-only and retrospective matching explicit, including edges."""
    if not times:
        raise ValueError("Cannot match an empty momentum series")
    index = bisect_left(times, tick)
    if index < len(times) and times[index] == tick:
        value = values[index]
        return {
            "previous_Nms": value, "next_Nms": value, "nearest_Nms": value,
            "previous_age_s": 0.0, "next_delay_s": 0.0,
            "interpolated_Nms": value, "sign_change_across_bracket": False,
        }
    previous = index - 1 if index > 0 else None
    following = index if index < len(times) else None
    age = tick - times[previous] if previous is not None else math.inf
    delay = times[following] - tick if following is not None else math.inf
    nearest = previous if age <= delay else following
    interpolated = None
    sign_change = False
    if previous is not None and following is not None:
        gap = times[following] - times[previous]
        if gap <= INTERPOLATION_GAP_MS:
            interpolated = values[previous] + (values[following] - values[previous]) * age / gap
        sign_change = values[previous] * values[following] < 0
    return {
        "previous_Nms": values[previous] if previous is not None else None,
        "next_Nms": values[following] if following is not None else None,
        "nearest_Nms": values[nearest],
        "previous_age_s": age / 1000 if math.isfinite(age) else None,
        "next_delay_s": delay / 1000 if math.isfinite(delay) else None,
        "interpolated_Nms": interpolated,
        "sign_change_across_bracket": sign_change,
    }


def coverage(torque, momentum, wheel, quarter):
    times = [tick for tick, _ in momentum]
    counts = Counter()
    for tick, value in torque:
        index = bisect_left(times, tick)
        exact = index < len(times) and times[index] == tick
        age = tick - times[index - 1] if index > 0 else math.inf
        delay = times[index] - tick if index < len(times) else math.inf
        counts["exact"] += exact
        counts["prior_within_20s"] += exact or age <= TOLERANCE_MS
        counts["symmetric_within_20s"] += min(age, delay) <= TOLERANCE_MS
        counts["nearest_is_future_within_20s"] += 0 < delay <= TOLERANCE_MS and delay < age
        counts["reconfig_threshold_50mNm"] += abs(value) >= 0.05
    return {
        "wheel": wheel, "quarter": quarter,
        "torque_rows": len(torque), "momentum_rows": len(momentum),
        "torque_median_cadence_s": median(b[0] - a[0] for a, b in zip(torque, torque[1:])) / 1000,
        "max_abs_torque_mNm": max(abs(value) for _, value in torque) * 1000,
        **counts,
    }


def september_peaks(torque, momentum, wheel):
    start, end = milliseconds("2015-09-01"), milliseconds("2015-10-01")
    strongest = sorted(
        ((tick, value) for tick, value in torque if start <= tick < end),
        key=lambda row: abs(row[1]), reverse=True,
    )[:5]
    times = [tick for tick, _ in momentum]
    values = [value for _, value in momentum]
    return [
        {
            "wheel": wheel, "rank": rank,
            "torque_ms_since_2000": tick, "torque_mNm": value * 1000,
            **momentum_match(times, values, tick),
        }
        for rank, (tick, value) in enumerate(strongest, start=1)
    ]


def analyze(data_directory):
    entries = read_manifest()
    sources = verify_inputs(data_directory, entries)
    summaries, peaks = [], []
    for wheel, torque_id, momentum_id in WHEELS:
        for quarter in QUARTERS:
            torque = read_series(data_directory, quarter, torque_id, "Nm")
            momentum = read_series(data_directory, quarter, momentum_id, "Nms")
            summaries.append(coverage(torque, momentum, wheel, quarter))
            if quarter == "2015_q3":
                peaks.extend(september_peaks(torque, momentum, wheel))
    keys = ("torque_rows", "exact", "prior_within_20s", "symmetric_within_20s",
            "nearest_is_future_within_20s", "reconfig_threshold_50mNm")
    return {
        "schema_version": 1,
        "settings": {
            "tolerance_ms": TOLERANCE_MS,
            "maximum_interpolation_bracket_ms": INTERPOLATION_GAP_MS,
            "epoch": "2000-01-01T00:00:00",
            "september_peak_count_per_wheel": 5,
        },
        "input_files": sources,
        "coverage": summaries,
        "totals": {key: sum(row[key] for row in summaries) for key in keys},
        "september_2015_peaks": peaks,
    }
