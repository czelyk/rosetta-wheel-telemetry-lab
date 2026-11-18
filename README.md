# Rosetta Wheel Telemetry Lab

Reproducible replay of ESA Rosetta reaction-wheel telemetry, comparing timestamp alignment and reproducing a published wheel-health observation.

The research question is whether a small engineering-telemetry product can retain the evidence used to identify a stressed wheel and its operating regions. This repository implements an archive alignment check and an equal-byte comparison of conventional telemetry products. A standard 256-byte daily summary retains the frozen peak and fixed-exceedance queries in this retrospective experiment. An embedded implementation remains future work, conditional on a distinct research question.

## Run

Use Python 3.10 or newer. All code uses the Python standard library. The recorded run used Python 3.12.10 on Windows. Run these commands from the repository directory.

```powershell
python fetch.py
python run.py --verify
python -m unittest discover -s tests -v
```

The first command downloads 48 pinned PDS table and label files, approximately 139 MB. Existing files are checked against their recorded size and SHA-256. If a local file fails verification, the error identifies it. Remove that damaged cache file and rerun the download. The data can be used offline after download.

To check an existing cache without network access, use `python fetch.py --verify-only`. Generated analysis goes to `runs/replay.json`. The checked-in reference is [results/recorded/replay.json](results/recorded/replay.json).

## Measured result

Three quarters and four wheels provide 12 channel pairs and 1,511,640 estimated-friction-torque rows. They are repeated measurements from one spacecraft.

| Alignment rule | Paired torque rows | Coverage |
| --- | ---: | ---: |
| Identical timestamps | 0 | 0% |
| Nearest momentum sample within 20 seconds, either direction | 1,506,828 | 99.68% |
| Current or earlier momentum sample within 20 seconds | 52,320 | 3.46% |

Most successful nearest matches use a momentum sample recorded later. That alignment supports retrospective analysis. Prior-only coverage reports the distinct information available at the torque timestamp. The 20-second tolerance is an exploratory analysis setting.

In September 2015, wheel C reaches 39.712 mNm absolute estimated friction torque. The maximum across the other three wheels is 16.6647 mNm. For C's five strongest samples, prior, nearest and bracket-interpolated momentum all have magnitude below 0.40 N·m·s. That observed range describes these samples. The archive cannot establish the exact momentum or zero-crossing instant between records.

The flight-dynamics team reported increased wheel C friction and operational restrictions on wheel speeds and zero crossings. Our replay reproduces a narrow part of that observation. [Zuiani et al., ISSFD 2015, section 2.3](https://issfd.org/2015/files/downloads/papers/098_Castellini.pdf)

## Research status

The previous exact-timestamp filter excluded usable retrospective evidence. After correcting it, the next experiment serialized and decoded four conventional products at equal daily byte allowances. Across 275 nearest-admitted days, a fixed-level bin summary retains all daily peaks and wheel/bin peak locations in 256 application bytes. It also preserves all 24 positive daily wheel/bin counts at the frozen 20 mNm level. This sufficiency follows from the retained statistics. The case for adding a more elaborate representation for those queries is closed. A Rosetta-specific downlink constraint has yet to be established.

To reproduce the byte-budget comparison, run `python run_retention.py --compare results/retention`. To inspect its 6,600 encoded packets without downloading the flight data, run `python run_retention.py --verify-packets results/retention`. [Detailed results and continuation decision](docs/RETENTION_RESULTS.md)

Current results cover archived estimated torque and measured momentum. Firmware timing, physical wheel measurements, predictive diagnosis and scientific originality remain unvalidated. The project is at exploratory research stage for IAC 2027.

- [Measurements and limitations](RESULTS.md)
- [Method and time-alignment semantics](docs/METHOD.md)
- [Next decision test](docs/NEXT_STEP.md)
- [Source records and access](docs/SOURCES.md)
- [Historical plans and evidence](history/README.md)

## Repository contents

| Path | Purpose |
| --- | --- |
| `fetch.py` | Download and verify the pinned public products |
| `rosetta.py` | Read PDS tables and calculate alignment and peak evidence |
| `run.py` | Execute the replay and compare it with recorded measurements |
| `data/manifest.tsv` | Source URLs, byte counts and SHA-256 digests |
| `results/recorded/` | Original alignment result and execution record |
| `retention.py`, `run_retention.py` | Byte-budget codecs, decoded queries and comparison runner |
| `results/retention/` | Encoded packets, per-packet index and measured comparison |
| `tests/` | Timestamp, alignment and integrity boundary checks |
| `history/` | Original screen and later Rosetta-only audit snapshot |

Raw archive files and generated runs are excluded from Git. The MIT license covers the authored code and documentation. Source-data rights and attribution are described in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
