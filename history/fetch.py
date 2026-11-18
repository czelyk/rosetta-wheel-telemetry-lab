from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen

BASE = "https://pds-smallbodies.astro.umd.edu/holdings/ro-x-hk-3-rwl-v1.0/data"
STREAMS = {
    "rwl_est_frict_torque": ("nacw0g05", "nacw0g0h", "nacw0g0t", "nacw0g15"),
    "rwl_meas_ang_mom": ("nacg0010", "nacg0011", "nacg0012", "nacg0013"),
}
QUARTERS = ("2014_q4", "2015_q3", "2016_q2")

def fetch(item):
    stream, quarter, parameter, extension = item
    name = f"ros_hk_{parameter}_{quarter}.{extension}"
    target = Path("data", quarter, name)
    target.parent.mkdir(parents=True, exist_ok=True)
    url = f"{BASE}/{stream}/{quarter}/{name}"
    if not target.exists():
        with urlopen(url, timeout=35) as response:
            content = response.read()
        if not content or content.lstrip().startswith(b"<"):
            raise ValueError(f"unexpected response for {url}")
        target.write_bytes(content)
    content = target.read_bytes()
    return f"{name}\t{len(content)}\t{sha256(content).hexdigest()}\t{url}"

if __name__ == "__main__":
    items = [(stream, q, parameter, ext) for q in QUARTERS
             for stream, parameters in STREAMS.items() for parameter in parameters
             for ext in ("lbl", "tab")]
    with ThreadPoolExecutor(max_workers=8) as pool:
        manifest = list(pool.map(fetch, items))
    Path("manifest.tsv").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(len(manifest), "downloaded or verified local")
