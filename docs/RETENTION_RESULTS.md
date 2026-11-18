# Conventional summaries at equal application-byte budgets

18 November 2026. The protocol was committed at `b6afe36` before policy scoring. The experiment ran on the existing 48 pinned archive files, with 1,511,640 torque rows and 275 calendar days. These periods were already inspected. All results are retrospective.

## Executed comparison

Four conventional products were actually serialized at 256, 512 and 1024 bytes per day across four wheels. The application envelope includes metadata, zero padding and CRC32. Each product was decoded before its queries were scored. The run produced 6,600 packets and 3,942,400 encoded bytes, plus a CSV index containing byte offsets, SHA-256 identities and measurements. This is an application-product experiment with no RF, CCSDS framing or MCU timing.

For nearest-momentum admission within 20 seconds, 1,506,828 paired rows remain. The full quantized admitted stream is the reference for each policy. At 256 bytes per day, the results are as follows.

| Product | Exact daily peak | Exact wheel set | Exact wheel/bin set | Exact positive 20 mNm count cells |
| --- | ---: | ---: | ---: | ---: |
| Equispaced records | 2/275 | 185/275 | 130/275 | 0/24 |
| Strongest records | 275/275 | 275/275 | 274/275 | 22/24 |
| Bin counts and signed extrema | 275/275 | 275/275 | 275/275 | 0/24 |
| Bin counts, absolute maximum and fixed 20 mNm count | 275/275 | 275/275 | 275/275 | 24/24 |

The 24 positive count cells are combinations of date, wheel and momentum bin, across 20 dates. They contain 239 admitted samples at or above 20 mNm. These are repeated archived measurements, with no inference of 239 independent faults. Count preservation is reported only when the decoded product determines the count exactly. Otherwise the result is a conservative interval, and the execution checks that every true count lies within its interval.

Both summary products store the peak statistics directly, and the fixed-level product also stores the primary exceedance count. Their exactness follows from their contents. The test establishes that these conventional sufficient statistics answer the chosen queries. It provides no evidence for a new algorithm.

## A different threshold exposes a bounded limitation

The protocol also froze a secondary query at 30 mNm. Two daily wheel/bin cells contain positive counts at that level. At 256 bytes, the strongest-record product determines both counts exactly. The fixed 20 mNm summary leaves both ambiguous. Its total interval width across the two cells is nine samples, with zero width elsewhere. Bin extrema also leave those two cells ambiguous, with total interval width 23.

At 1024 bytes, strongest-record retention also determines all 24 positive 20 mNm counts and all 275 peak-location sets exactly. At the lower budgets, equal quantized peaks can span more retained locations than fit in the selected strongest records, accounting for the 274/275 location result.

The two bin products keep their frozen 256-byte content and pad at larger allowances. A conventional extension could spend the unused allowance on another threshold counter. The 28 additional two-byte counters alone would occupy 56 bytes. Thus their secondary ambiguity at a larger budget must not be interpreted as an inherent limit of conventional summaries. This experiment supplies no global optimality claim for any policy.

## Alignment and quantization matter

Of the nearest-admitted rows, 1,454,716 use momentum recorded later than torque. The products therefore describe a retrospective archive analysis. An eventual onboard implementation would need an actual acquisition path and explicitly bounded waiting or a different association rule.

The unfiltered torque archive contains 261 samples at or above 20 mNm. Nearest-within-20-seconds admission excludes 22 of them and retains 239. All four samples at or above 30 mNm remain admitted. Exact retention within the admitted stream cannot establish preservation of the excluded high-torque evidence.

The strict current-or-prior 20-second rule admits only 52,320 rows across 77 nonempty days. It contains zero samples at either exploratory exceedance level. Its perfect summary scores cannot validate preservation of the high-torque cases that this admission rule excludes.

Rounding to 0.01 Nms changes bin membership for 280 nearest-admitted samples and two prior-only samples. Maximum rounding error is approximately 0.005 Nms and 0.005 mNm. Neither exploratory torque-threshold classification changes on admitted records. Preservation scores refer to the quantized admitted stream. They do not establish preservation of every original unpaired observation or sub-sample physical wheel behavior.

## Selection consequence

**NO GO for proposing an additional representation solely to answer these frozen peak and fixed-count queries.** A conventional 256-byte product already retains their answers. The secondary query is better served by another conventional product at the same 256-byte budget, or potentially by extra counters when more bytes are available. There is still no documented Rosetta allocation or operator benefit that would justify a more elaborate method.

The earlier reassessment correctly reopened the usable-data question. This comparison resolves the next baseline gate against an extra method for the current query contract. It does not reject every possible Rosetta study. Further research would need a separately documented query, operational consequence and competent alternative before another implementation campaign.

No independent scientific reviewer has cleared this result. Physical diagnosis, spacecraft resource requirements, a novel engineering contribution and a final IAC selection remain open.

## Reproduce

From the repository directory, run the following after populating the flight-data cache.

```powershell
python run_retention.py --compare results/retention
python -m unittest discover -s tests -v
```

The packet artifact can also be checked without the source-data cache.

```powershell
python run_retention.py --verify-packets results/retention
```

[Frozen protocol](RETENTION_PROTOCOL.md) · [All aggregate results and input identities](../results/retention/summary.json) · [Per-packet measurements](../results/retention/packets.csv) · [Encoded packet stream](../results/retention/packets.bin)
