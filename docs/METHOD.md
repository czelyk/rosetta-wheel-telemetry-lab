# Method

## Inputs

The dataset identifier is `RO-X-HK-3-RWL-V1.0`, Rosetta Reaction Wheel Engineering Data. Three quarters are pinned: 2014 Q4, 2015 Q3 and 2016 Q2. Each quarter includes estimated friction torque and measured angular momentum for wheels A through D.

The manifest contains 24 ASCII tables and their 24 PDS3 labels. Table time is `TIME OF MEASUREMENT` with millisecond timestamps. Labelled torque units are Nm and momentum units Nms. Reported torque is converted to mNm by multiplying by 1,000. The analysis retains signed values and uses magnitude for peak ranking.

Downloaded content is accepted only when both size and SHA-256 match the pinned manifest. Existing cache files are checked too. The parser checks increasing timestamps, finite values, declared row counts and value units. Milliseconds are represented as integer offsets from 2000-01-01, using the supplied archive times without changing time scales or estimating clock corrections.

## Alignment rules

- Exact alignment requires the same recorded millisecond.
- Symmetric alignment accepts a momentum record within an inclusive 20,000 ms on either side of a torque record. If neighbors are equally distant, the earlier record wins.
- Prior-only coverage accepts an exact record or a preceding record no older than 20,000 ms.
- Peak analysis additionally reports the preceding and following values, their time offsets, the nearest value and a linear bracket estimate. Interpolation requires both neighbors and a bracket no longer than 128,000 ms. Exact matches use the value directly. Missing neighbors are represented by JSON null.

The tolerance and interpolation limits are declared analysis settings. They are separate from any spacecraft requirement, acquisition accuracy or physical response time. Nearest and interpolated results can use future archive samples, so only prior-only coverage characterizes information available at the torque timestamp.

## Peak selection

For September 2015, rank each wheel's torque records by descending absolute value and retain five. Select these rows before matching momentum. Equal-magnitude ties preserve archive order. Report the signed torque, signed momentum alternatives and any sign change between bracket endpoints. Sign changes are a retrospective indicator with archive-resolution uncertainty.

The comparison was designed after the initial archive screen. The initial plan had called 2016 Q2 held out, but its coverage had already been examined before repository packaging. None of the existing three-quarter coverage results is presented as a fresh validation set. A later telemetry-policy comparison needs a new frozen protocol and explicitly identified validation periods.

## Interpretation

Archive row counts measure coverage. They are correlated samples and should not be converted into fault or acceptance probabilities. Estimated friction is a spacecraft-derived parameter. Its association with momentum is useful for replaying documented engineering evidence, while causal fault diagnosis requires additional measurements and a validated physical model.
