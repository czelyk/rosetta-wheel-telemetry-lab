# Equal-budget conventional-baseline experiment

18 November 2026. Frozen before policy scoring on branch `codex/equal-budget-baselines`.

## Question and decision

Can conventional telemetry products preserve daily wheel-health evidence at the same encoded application-byte budget? The candidate contribution needs a benefit beyond these products. If a conventional sufficient summary retains the frozen questions, retire the claim that these questions require a more elaborate representation. Retain any measured limitations of that summary.

The existing 2014 Q4, 2015 Q3 and 2016 Q2 archive products have already been inspected. All scoring in this step is retrospective. No month is newly held out. The experiment is a baseline sufficiency check, with no new proposed algorithm.

## Admitted data and quantization

Use the pinned 48 input files. Group by the archive UTC calendar date of the torque timestamp. Evaluate two separate admitted streams. The first uses the nearest momentum sample within an inclusive 20 seconds, with ties assigned to the earlier sample. The second requires a current or prior sample no older than 20 seconds. Evaluate all methods on exactly the same admitted stream within each alignment.

Quantize torque to signed 16-bit units of 0.01 mNm, and momentum to signed 16-bit units of 0.01 Nms, using Python's round-to-nearest with ties-to-even. Reject out-of-range values. Evaluate preservation against the complete quantized admitted stream. Record maximum quantization error and differences in bin membership and threshold classification versus the original paired values.

Momentum bins are signed intervals with edges at -20, -5, -0.5, 0.5, 5 and 20 Nms. Lower edges are inclusive. These are exploratory bins that distinguish near-zero and progressively higher magnitude. They are independent of a verified mission limit. The exploratory torque exceedance levels are 20 and 30 mNm inclusive. The 50 mNm flight reconfiguration threshold remains a separate archived result.

## Frozen daily questions

For each nonempty admitted day, recover the largest absolute quantized torque, the set of wheel IDs attaining it, and the set of wheel/momentum-bin pairs attaining it. Equal values remain ties. Also recover the number of records at or above 20 mNm and 30 mNm in each of the 28 wheel/bin cells. Report conservative lower and upper bounds where a representation cannot determine a count. Verify every bound against the full-stream count.

## Application-byte accounting

Budgets are 256, 512 and 1024 bytes per day across all four wheels. These are laboratory allowances. The 256-byte minimum was selected to fit one conventional 28-cell summary including metadata and integrity check. No Rosetta allocation is inferred.

Every packet has a 28-byte header containing four-byte magic, one-byte format version, one-byte policy ID, four-byte day anchor in seconds since 2000-01-01, two-byte record count, four two-byte admitted counts and four two-byte unpaired counts. Each packet ends with a four-byte CRC32 for accidental corruption. Zero padding fills any unused allowance, and the CRC covers the header, body and padding. No link-layer or CCSDS framing is modeled. Its common overhead is outside the declared application allowance.

A paired-record entry is nine bytes containing wheel ID, four-byte torque timestamp offset within the day, two-byte signed torque and two-byte signed momentum. A summary cell is eight bytes and explicitly carries wheel ID and bin ID. Thus each conventional 28-cell product consumes 256 bytes including the common envelope.

## Competent products

1. Equispaced records. Allocate record slots across wheels as evenly as available admitted samples permit. Within each wheel choose records nearest to uniformly spaced time targets across the day. Retain unique selected records. Sparse data can leave unused padding.
2. Strongest records. Retain the largest absolute torques until record slots are exhausted, resolving ties by timestamp and wheel ID. This protects extreme events. If the weakest retained value is below an exceedance level, every exceedance at that level is retained and its count is known.
3. Bin extrema. Store count, signed minimum torque and signed maximum torque in each wheel/bin cell. These are conventional statistics. Derive bounds for exceedance counts from the range and sample count.
4. Fixed-level bin counts. Store count, maximum absolute torque and number at or above 20 mNm in each cell. This standard fixed-limit summary directly answers the 20 mNm question. Bound the secondary 30 mNm count from the retained count and maximum.

Decode each byte packet through a separate parsing function and score only its decoded contents. Include an empty cell and all four wheel metadata fields even when a wheel is absent. Days with no torque rows at all do not create a packet. Days with torque but no admitted pair are recorded but excluded from nonempty-stream query scores.

## Metrics and interpretation

Record per-packet size, SHA-256, byte offset, admitted and unpaired counts, peak-value equality, wheel-set equality, wheel/bin-set equality, exact count cells, exact positive count cells and uncertainty widths. Aggregate by alignment, budget and policy. Keep the binary packet stream and index CSV so the reported budget can be independently checked.

A summary that stores the queried statistics succeeds by construction. That result establishes the strength of the baseline for this frozen question. It supplies no independent fault diagnosis or scientific novelty. The 30 mNm secondary question measures a declared limitation when the threshold-specific summary is reused. Sparse prior-only coverage must be reported alongside apparent preservation scores.

## Next decision

If simple products suffice, close this experiment with a bounded negative selection result for an extra representation. A different question would require a documented operational need that those products cannot satisfy. If the comparison exposes a useful difference, first test it on newly designated periods under a new frozen protocol and review the closest prior work before building MCU firmware.
