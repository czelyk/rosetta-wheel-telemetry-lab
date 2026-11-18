"""Download the public PDS products pinned in data/manifest.tsv."""

import argparse
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

from rosetta import ROOT, read_manifest, verify_content, verify_inputs


def fetch_entry(entry, data_directory):
    destination = data_directory / entry["path"]
    if destination.exists():
        verify_content(destination.read_bytes(), entry)
        return
    with urlopen(entry["url"], timeout=60) as response:
        content = response.read()
    verify_content(content, entry)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".part", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--verify-only", action="store_true", help="Verify local files without networking")
    args = parser.parse_args()
    entries = read_manifest()
    if not args.verify_only:
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda entry: fetch_entry(entry, args.data_dir), entries.values()))
    verify_inputs(args.data_dir, entries)
    print(f"Verified all {len(entries)} pinned files.")


if __name__ == "__main__":
    main()
