"""Replay all pinned data and optionally compare with the recorded result."""

import argparse
import json
from pathlib import Path

from rosetta import ROOT, analyze


def verify_recorded(result):
    recorded = ROOT / "results" / "recorded" / "replay.json"
    expected = json.loads(recorded.read_text(encoding="utf-8"))
    if result != expected:
        raise ValueError("Replay differs from results/recorded/replay.json")
    history = ROOT / "history" / "20261117-rosetta-audit.json"
    previous = json.loads(history.read_text(encoding="utf-8"))["rosetta"]
    rows = {(row["wheel"], row["quarter"]): row for row in result["coverage"]}
    for old in previous:
        current = rows[old["wheel"], old["quarter"]]
        for field, value in old.items():
            if field == "september_2015_max_abs_torque_samples":
                peaks = [row for row in result["september_2015_peaks"] if row["wheel"] == old["wheel"]]
                if len(peaks) != len(value):
                    raise ValueError("Historical peak count differs")
                for expected_peak, peak in zip(value, peaks):
                    if any(peak[name] != metric for name, metric in expected_peak.items()):
                        raise ValueError(f"Historical peak measurement differs for wheel {old['wheel']}")
            elif current[field] != value:
                raise ValueError(f"Historical coverage differs for {old['wheel']} {old['quarter']} {field}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=ROOT / "runs" / "replay.json")
    parser.add_argument("--verify", action="store_true", help="Compare with the checked-in result")
    args = parser.parse_args()
    recorded = ROOT / "results" / "recorded" / "replay.json"
    if args.output.resolve() == recorded.resolve():
        parser.error("Choose a generated output path outside the recorded result")
    result = analyze(args.data_dir)
    if args.verify:
        verify_recorded(result)
        print("All recorded measurements reproduced exactly.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    totals = result["totals"]
    print(f"Verified {len(result['input_files'])} source files.")
    print(f"Analyzed {totals['torque_rows']:,} torque rows in 12 wheel/quarter pairs.")
    print(f"Exact matches: {totals['exact']:,}")
    print(f"Within 20 s, either direction: {totals['symmetric_within_20s']:,}")
    print(f"Within 20 s, prior-only: {totals['prior_within_20s']:,}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
