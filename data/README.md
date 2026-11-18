# Flight-data cache

`manifest.tsv` pins the 48 required PDS products with filename, byte count, SHA-256 and source URL. The total is 138,978,944 bytes. Quarters are stored in `2014_q4/`, `2015_q3/` and `2016_q2/`.

Run `python fetch.py` from the repository directory to populate this cache. Run `python fetch.py --verify-only` to check it offline. Python 3.10 or newer is sufficient, with no package installation.

The cache directories are excluded from Git. Copying this repository to another computer requires downloading or copying the same pinned files. The analysis and verification commands accept `--data-dir` for a cache in another location.

The manifest retains the original byte identities, including source line endings. PDS labels contain dataset identity, product row counts, parameter descriptions, time coverage and units. Preserve labels alongside tables.
