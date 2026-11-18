# Recorded replay

18 November 2026. Python 3.12.10 on Windows, using the standard library. All 48 source file lengths and SHA-256 digests were verified before analysis. PDS row counts and value units were also checked.

## Alignment

| Metric | Count |
| --- | ---: |
| Torque rows across 12 wheel/quarter pairs | 1,511,640 |
| Identical torque and momentum timestamps | 0 |
| Nearest momentum within 20 seconds | 1,506,828 |
| Current or prior momentum within 20 seconds | 52,320 |
| Nearest sample is later and within 20 seconds | 1,454,716 |
| Torque rows at or above 50 mNm magnitude | 0 |

Torque sampling has a median cadence of 64 seconds in each of the 12 pairs. A common channel offset is approximately 12 seconds. These are properties of the archived products. The files do not measure native onboard acquisition cadence or independent hardware synchronization error.

The 50 mNm value comes from the flight-dynamics report's automatic wheel reconfiguration threshold. That report also describes operational wheel-speed restrictions before the threshold was reached. Absence of a 50 mNm archive sample therefore leaves a retrospective wheel-health study open. Shorter excursions could fall between archive samples. [Zuiani et al., section 2.3](https://issfd.org/2015/files/downloads/papers/098_Castellini.pdf)

## September 2015

The month was selected in the follow-up plan because the mission paper describes wheel C's condition in that period. It is an exploratory comparison on previously inspected 2015 Q3 data.

| Wheel | Largest absolute estimated friction torque |
| --- | ---: |
| A | 15.4717 mNm |
| B | 16.6647 mNm |
| C | 39.7120 mNm |
| D | 16.3309 mNm |

For wheel C's five strongest samples, prior, nearest and linearly interpolated momentum all lie within magnitude 0.40 N·m·s. Prior samples are approximately 52 seconds earlier, and nearest samples approximately 12 seconds later. Three of the five brackets contain opposite-sign momentum values. These are five samples from the same spacecraft and month, with no claim of five independent failures.

Linear interpolation is reported only when the two bracketing momentum samples are at most 128 seconds apart. Interpolation assumes the value changes linearly between them. It does not independently observe wheel motion between records. A sign change in a bracket cannot establish a torque-peak coincidence with the exact crossing.

## Reproduction and evidence

The standalone replay was compared against the earlier audit's 12 coverage rows and all 20 peak records. Every shared field matched. The original audit's Rosetta-only output and the SHA-256 of its parent result are retained in [the historical snapshot](history/20261117-rosetta-audit.json).

Eight boundary tests passed, covering exact timestamps, future-versus-prior matches, inclusive tolerance, nearest-neighbor ties, excessive interpolation gaps, missing brackets, integer time conversion and same-length corrupted content. The downloader fetched one label from the public PDS URL, verified its checksum and reused the validated cache. The full 48-file download was already available locally and was verified offline during packaging.

Run `python run.py --verify` after `python fetch.py`. The check compares the complete new analysis with [the recorded JSON](results/recorded/replay.json) and checks shared measurements against the historical audit. Successful reproduction establishes consistency with those records. It provides no new physical validation.

## Open contribution

The replay recovers useful evidence discarded by exact matching. The subsequent [byte-budget experiment](docs/RETENTION_RESULTS.md) executed the conventional-baseline comparison and found that a standard 256-byte summary already preserves the primary frozen questions. The original alignment measurements above remain the record of the first stage. The later result closes the current case for an additional representation answering those same queries.
