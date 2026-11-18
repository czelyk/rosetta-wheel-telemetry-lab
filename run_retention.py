"""Execute the frozen equal-budget conventional-baseline comparison."""

import argparse
import csv
import hashlib
import json
import platform
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path

from retention import ALIGNMENTS, BUDGETS, DAY_MS, POLICIES, decode, encode, quantize, reference_queries, region, score
from rosetta import EPOCH, QUARTERS, ROOT, WHEELS, read_manifest, read_series, verify_inputs


def admitted_streams(data_directory):
    sources = verify_inputs(data_directory, read_manifest())
    streams = {mode: defaultdict(list) for mode in ALIGNMENTS}
    raw_counts = defaultdict(lambda: [0] * 4)
    raw_limits = Counter()
    checks = {mode: Counter() for mode in ALIGNMENTS}
    raw_edges = (-20, -5, -0.5, 0.5, 5, 20)
    for wheel, (_, torque_id, momentum_id) in enumerate(WHEELS):
        for quarter in QUARTERS:
            torque = read_series(data_directory, quarter, torque_id, "Nm")
            momentum = read_series(data_directory, quarter, momentum_id, "Nms")
            times = [tick for tick, _ in momentum]
            for tick, value in torque:
                day = tick // DAY_MS
                raw_counts[day][wheel] += 1
                for level in (20, 30):
                    raw_limits[f"source_rows_ge{level}"] += abs(value) * 1000 >= level
                index = bisect_left(times, tick)
                neighbors = momentum[max(0, index - 1):index + 1]
                nearest = min(neighbors, key=lambda row: (abs(row[0] - tick), row[0]))
                prior_index = index if index < len(times) and times[index] == tick else index - 1
                prior = momentum[prior_index] if prior_index >= 0 else None
                pairs = (("nearest20", nearest), ("prior20", prior))
                for mode, match in pairs:
                    if match is None or abs(match[0] - tick) > 20_000:
                        continue
                    sample = quantize(wheel, tick, value, match[1])
                    streams[mode][day].append(sample)
                    audit = checks[mode]
                    audit["admitted_rows"] += 1
                    audit["future_momentum_rows"] += match[0] > tick
                    audit["momentum_bin_changes"] += region(sample.momentum) != bisect_right(raw_edges, match[1])
                    audit["max_torque_error_mNm"] = max(audit["max_torque_error_mNm"], abs(sample.torque * 0.01 - value * 1000))
                    audit["max_momentum_error_Nms"] = max(audit["max_momentum_error_Nms"], abs(sample.momentum * 0.01 - match[1]))
                    for level in (20, 30):
                        audit[f"admitted_rows_ge{level}"] += abs(sample.torque) >= level * 100
                        audit[f"threshold_{level}_classification_changes"] += ((abs(sample.torque) >= level * 100)
                                                                               != (abs(value) * 1000 >= level))
    for audit in checks.values():
        audit.update(raw_limits)
        for level in (20, 30):
            audit[f"unpaired_rows_ge{level}"] = raw_limits[f"source_rows_ge{level}"] - audit[f"admitted_rows_ge{level}"]
    return streams, raw_counts, checks, sources


def execute(data_directory, destination):
    streams, raw_counts, admission, sources = admitted_streams(data_directory)
    destination.mkdir(parents=True, exist_ok=True)
    aggregates = defaultdict(Counter)
    index_rows = []
    offset = 0
    with (destination / "packets.bin").open("wb") as binary:
        for mode in ALIGNMENTS:
            for day, counts in sorted(raw_counts.items()):
                samples = streams[mode][day]
                truth = reference_queries(samples)
                for budget in BUDGETS:
                    for policy in POLICIES:
                        packet = encode(samples, counts, day, mode, policy, budget)
                        decoded = decode(packet)
                        expected_counts = Counter(sample.wheel for sample in samples)
                        if decoded["admitted"] != [expected_counts[wheel] for wheel in range(4)]:
                            raise ValueError("Decoded admission metadata differs")
                        metrics = score(decoded, truth)
                        row = {
                            "alignment": mode, "date": (EPOCH + timedelta(days=day)).date().isoformat(),
                            "budget_bytes": budget, "policy": policy,
                            "offset": offset, "encoded_bytes": len(packet),
                            "sha256": hashlib.sha256(packet).hexdigest(),
                            "raw_torque_rows": sum(counts), "admitted_rows": len(samples),
                            "unpaired_rows": sum(counts) - len(samples), **metrics,
                        }
                        index_rows.append(row)
                        group = aggregates[mode, budget, policy]
                        group["packets"] += 1
                        group["nonempty_days"] += metrics["nonempty"]
                        if metrics["nonempty"]:
                            group.update({key: value for key, value in metrics.items() if key != "nonempty"})
                        binary.write(packet)
                        offset += len(packet)
    index = destination / "packets.csv"
    with index.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(index_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(index_rows)
    summaries = [
        {"alignment": mode, "budget_bytes": budget, "policy": policy, **metrics}
        for (mode, budget, policy), metrics in sorted(aggregates.items())
    ]
    report = {
        "schema_version": 1, "evaluation": "retrospective on previously inspected archive quarters",
        "protocol_sha256": hashlib.sha256((ROOT / "docs/RETENTION_PROTOCOL.md").read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                          for name in ("retention.py", "run_retention.py", "rosetta.py")},
        "input_files": sources,
        "raw_torque_rows": sum(sum(counts) for counts in raw_counts.values()),
        "days_with_torque": len(raw_counts), "admission_and_quantization": admission,
        "summary": summaries,
        "artifacts": {name: {"bytes": (destination / name).stat().st_size,
                              "sha256": hashlib.sha256((destination / name).read_bytes()).hexdigest()}
                      for name in ("packets.bin", "packets.csv")},
    }
    return report


def verify_packets(destination):
    groups = defaultdict(Counter)
    expected_offset = 0
    with (destination / "packets.bin").open("rb") as stream, (destination / "packets.csv").open(encoding="utf-8", newline="") as index:
        for row in csv.DictReader(index):
            size = int(row["encoded_bytes"])
            if int(row["offset"]) != expected_offset or size != int(row["budget_bytes"]):
                raise ValueError("Packet offsets or budget accounting differ")
            packet = stream.read(size)
            if len(packet) != size or hashlib.sha256(packet).hexdigest() != row["sha256"]:
                raise ValueError("Recorded packet identity differs")
            decoded = decode(packet)
            date = (EPOCH + timedelta(days=decoded["day"])).date().isoformat()
            if (decoded["policy"], decoded["alignment"], date) != (row["policy"], row["alignment"], row["date"]):
                raise ValueError("Decoded packet identity differs")
            if sum(decoded["admitted"]) != int(row["admitted_rows"]) or sum(decoded["unpaired"]) != int(row["unpaired_rows"]):
                raise ValueError("Recorded metadata counts differ")
            group = groups[row["alignment"], int(row["budget_bytes"]), row["policy"]]
            group["packets"] += 1
            group["nonempty_days"] += int(row["nonempty"])
            if int(row["nonempty"]):
                group.update({name: int(row[name]) for name in row
                              if name in ("peak_exact", "wheel_exact", "wheel_region_exact", "peak_ge20")
                              or name.startswith("count20_") or name.startswith("count30_")})
            expected_offset += size
        if stream.read(1):
            raise ValueError("Unindexed packet bytes remain")
    recorded = json.loads((destination / "summary.json").read_text(encoding="utf-8"))
    actual = [{"alignment": mode, "budget_bytes": budget, "policy": policy, **metrics}
              for (mode, budget, policy), metrics in sorted(groups.items())]
    if actual != recorded["summary"]:
        raise ValueError("Packet-index aggregates differ from recorded summary")
    for name, identity in recorded["artifacts"].items():
        content = (destination / name).read_bytes()
        if len(content) != identity["bytes"] or hashlib.sha256(content).hexdigest() != identity["sha256"]:
            raise ValueError(f"Artifact identity differs for {name}")
    print(f"Verified packet identities, offsets, CRCs, budgets and aggregates for {sum(g['packets'] for g in groups.values())} packets.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=ROOT / "runs" / "retention")
    parser.add_argument("--verify-packets", type=Path, help="Audit a recorded packet stream without downloading data")
    parser.add_argument("--compare", type=Path, help="Compare replay metrics and packets with a recorded output")
    args = parser.parse_args()
    if args.verify_packets:
        verify_packets(args.verify_packets)
        return
    recorded = ROOT / "results" / "retention"
    if args.output.resolve() == recorded.resolve():
        parser.error("Use a generated output directory outside results/retention")
    result = execute(args.data_dir, args.output)
    if args.compare:
        expected = json.loads((args.compare / "summary.json").read_text(encoding="utf-8"))
        for name in ("summary", "artifacts", "admission_and_quantization", "input_files", "raw_torque_rows", "days_with_torque"):
            if result[name] != expected[name]:
                raise ValueError(f"Retention replay differs in {name}")
        print("All recorded retention measurements and packet bytes reproduced exactly.")
    (args.output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    verify_packets(args.output)
    for row in result["summary"]:
        if row["alignment"] == "nearest20" and row["budget_bytes"] == 256:
            print(row["policy"], "peak", row["peak_exact"], "/", row["nonempty_days"],
                  "wheel/region", row["wheel_region_exact"], "count20 positive exact",
                  row["count20_positive_exact"], "/", row["count20_positive_cells"])


if __name__ == "__main__":
    main()
