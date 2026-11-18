# Rosetta reaction-wheel telemetry screening plan

## Decision and scope

Can a small embedded engineering-telemetry product preserve the wheel and momentum regions responsible for persistent high estimated drag, and therefore preserve the ground operations choice of which wheel and momentum region to constrain? ESA flight dynamics used estimated wheel friction versus measured momentum to adjust off-loading and avoid high-speed operation and zero crossings. No bandwidth constraint is known for Rosetta. This is a replay about prospective constrained designs, not a counterfactual diagnosis of the original mission or a claim of an actual reconfiguration.

## Prior and counterargument

Rosetta operators already used full-resolution scatter plots and maintenance trend diagnostics. JPL's Deep Space One already defined low-rate snapshots, mission-dependent alarm limits, and circular high-rate episode records. Compare periodic paired samples, existing alarm/episode retention, and conventional per-wheel momentum-bin count and min/max. A fourth candidate adds occupancy/exceedance counts per bin. Fixed limits with event-only logs can beat all sketches whenever events are rare and the thresholds are stable. If the simplest fixed-limit event retention or bin count and extrema preserves the chosen decisions over the data at comparable bytes, reject a new method. Do not treat a bytes-versus-accuracy curve from an invented threshold as independently sufficient novelty.

## Precommitted pilot

Use raw PDS archive pairs only at exact timestamp matches. Use 2014 Q4 as development data and 2015 Q3 as an exploratory comparator that contains the published degradation window. Preserve 2016 Q2 as held out. For page/packet accounting include wheel identity, window time anchor, record counts, and any different per-record cost. Test daily estimates of largest abs friction and near-zero / intermediate / high measured-momentum regions. Published 50 mNm autonomous case is separate from analyst sensitivity probes at 20, 30 and 40 mNm. Measure sample and occupancy coverage first, using archive-resolution truth only. If archive cadence is insufficient to identify excursions or the real action predicate is unavailable and the methods only differ on exploratory proxies, the candidate cannot pass strong selection.
