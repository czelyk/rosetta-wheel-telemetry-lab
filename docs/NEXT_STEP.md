# Next decision test

The planned conventional-baseline experiment is complete. Its [frozen protocol](RETENTION_PROTOCOL.md) and [executed result](RETENTION_RESULTS.md) are recorded. A standard 256-byte summary preserves the primary frozen questions, so adding another representation for that purpose has no demonstrated justification.

The checklist below preserves the original decision sequence. The baseline comparison in steps 1 through 4 was executed on previously inspected periods, with that retrospective scope reported explicitly. Newly held-out validation, a new method and an MCU recorder remain unperformed. The conventional-baseline gate already defeats the current extra-representation claim.

1. Define the retrospective question from the mission report, including the wheel ranking and operating regions to preserve. State which part can be checked against the archived samples. Use a range of data allowances unless an actual mission allocation is documented. A chosen laboratory allowance must be labelled as such.
2. Freeze the timestamp association, momentum bins, quantization, time-window lengths and encoded fields before scoring a validation period. Include wheel identity, window time, count fields and metadata in every byte total.
3. Implement competent comparisons consisting of periodic paired records, a fixed-limit event record, and per-wheel momentum-bin counts with torque extrema. Use the same admitted measurements and record any dependence on future samples.
4. Before adding an elaborate representation, test whether the simple summaries already retain the defined wheel ranking and region evidence. Score errors on archive-level queries and sensitivity to the alignment assumptions. Include additional months with a protocol that distinguishes already inspected data from fresh validation.
5. Continue to an embedded recorder only if the result changes a useful engineering choice or establishes an informative applicability limit beyond the existing summaries. Otherwise retain the measured baseline result and retire the extra method.

There is no demonstrated Rosetta bandwidth shortfall, selected byte allowance, new algorithm, physical wheel experiment or MCU timing result in the current repository. Physical hardware is unnecessary for the next archive comparison. If that comparison supports continued work, a bounded C implementation can replay the same inputs on an obtainable MCU and measure actual encoded bytes, peak memory and execution cost. Hardware timing would describe the tested MCU implementation.

A next research step requires a documented operational query that the competent conventional products cannot already answer adequately within a justified budget. Establish that requirement before selecting another representation or building firmware. Ahmet must reproduce the decisive experiment, review sources and own the scientific interpretation used in a paper.
