# Historical evidence

The original 16 November 2026 screen is retained in `coverage.py`, `coverage.txt`, `fetch.py` and `experiment-plan.md`. Its exact-timestamp restriction excluded every pair. The original downloader recorded local checksums after fetching files. The repository's root downloader instead checks downloads against the pinned manifest.

`20261117-followup-plan-tr.md` preserves the Turkish plan for the later month-specific check. `20261117-rosetta-audit.json` contains only the Rosetta results extracted from the broader local audit. It includes the SHA-256 of the complete parent JSON for provenance. The broader audit contained other project decisions and remains outside this repository.

The current standalone replay reproduces every shared field from that Rosetta snapshot. It adds archive-unit and row-count validation, explicit edge handling for missing momentum neighbors, and an executable verification path.

The superseded exact-match rule and the later correction are documented together so a reader can inspect the reason for reopening the data analysis.
