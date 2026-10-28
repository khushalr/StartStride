"""Download ORIGINAL TTC streetcar delay records from Toronto Open Data.

Never generates synthetic examples. Fail with an error when source is unavailable.
Use --fallback-uoft to explicitly allow an archived University of Toronto copy
of the original City of Toronto streetcar delay data (through 2025 only).

Example: python src/real_data/download_streetcar.py --out outputs/real/source.csv
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

API_BASE = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action"
OPEN_DATA_PAGE = "https://open.toronto.ca/dataset/ttc-streetcar-delay-data/"
UOFT_ARCHIVE = "https://pages.scinet.utoronto.ca/~afedosee/ttc-streetcar-delay-data-2014-2025.zip"
USER_AGENT = "StopStride-portfolio-research/1.0 (City of Toronto Open Data; attributable analysis)"
MAX_BYTES = 35_000_000  # CSV source; bound memory and reject unusually large downloads


def fetch(url: str, max_bytes: int = MAX_BYTES) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(request, timeout=35) as response:
        payload = response.read(max_bytes + 1)
        if len(payload) > max_bytes:
            raise ValueError("Source exceeded maximum allowed file size")
        return payload


def _city_package() -> dict:
    # CKAN package_search is more resilient to dataset slug changes than package_show.
    query = urlencode({"q": "TTC Streetcar Delay Data", "rows": 20})
    body = json.loads(fetch(f"{API_BASE}/package_search?{query}", 3_000_000))
    if not body.get("success"):
        raise ValueError("Toronto CKAN returned success=false")
    results = body.get("result", {}).get("results", [])
    matches = [x for x in results if str(x.get("title", "")).strip().lower()
               == "ttc streetcar delay data"]
    if len(matches) != 1:
        raise ValueError(f"Expected one official TTC streetcar dataset; found {len(matches)}")
    return matches[0]


def _is_city_url(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return urlparse(url).scheme == "https" and (host == "toronto.ca" or
           host.endswith(".toronto.ca") or host.endswith(".prod-toronto.ca"))


def download_official() -> tuple[bytes, str, str]:
    package = _city_package()
    resources = package.get("resources", [])
    csv_resources = [
        r for r in resources
        if str(r.get("format", "")).upper() == "CSV"
        and "since 2025" in str(r.get("name", "")).lower()
        and (r.get("url") or r.get("resource_url"))
    ]
    if len(csv_resources) != 1:
        raise ValueError(f"Expected one 2025+ CSV resource; found {len(csv_resources)}")
    resource = csv_resources[0]
    url = resource.get("url") or resource.get("resource_url")
    if not _is_city_url(url):
        raise ValueError(f"Unexpected official resource host: {url}")
    return fetch(url), url, str(resource.get("last_modified") or "not supplied")


def download_uoft_2025() -> tuple[bytes, str, str]:
    import zipfile
    archive = fetch(UOFT_ARCHIVE, max_bytes=90_000_000)
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        names = [n for n in zf.namelist()
                 if n.endswith("ttc-streetcar-delay-data-2025.csv") and ".." not in n]
        if len(names) != 1:
            raise ValueError("Archive is missing unique 2025 streetcar CSV")
        return zf.read(names[0]), UOFT_ARCHIVE, "archival copy, through 2025"


def _validate_streetcar_csv(payload: bytes) -> None:
    decoded = payload.decode("utf-8-sig", errors="replace")
    headers = next(csv.reader(io.StringIO(decoded)))
    normalized = {h.strip().lower().replace('report.date','date').replace('min.delay','min delay') for h in headers}
    if not {"date", "route", "time", "min delay"}.issubset(normalized):
        raise ValueError(f"NOT streetcar format; actual CSV columns are {headers}")
    if sum(1 for _ in io.StringIO(decoded)) < 100:
        raise ValueError("TTC streetcar CSV unexpectedly small; refusing to publish")


def save_real_csv(out: Path, fallback_uoft: bool = False) -> dict:
    errors = []
    try:
        payload, source, modified = download_official()
        _validate_streetcar_csv(payload)
        method = "official Toronto Open Data CKAN CSV"
    except Exception as exc:
        errors.append(f"Official CKAN error: {type(exc).__name__}: {exc}")
        print(errors[-1], flush=True)
        if not fallback_uoft:
            raise RuntimeError("Official download failed or returned non-streetcar data; "
                               "no synthetic fallback. " + errors[-1]) from exc
        payload, source, modified = download_uoft_2025()
        _validate_streetcar_csv(payload)
        method = "University of Toronto archived copy of TTC records (2025 only)"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    meta = {
        "origin": "REAL",
        "source": source,
        "official_dataset_page": OPEN_DATA_PAGE,
        "retrieval": method,
        "last_modified_at_source": modified,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source_bytes": len(payload),
    }
    out.with_suffix(".source.json").write_text(json.dumps(meta, indent=2)+"\\n", encoding="utf-8")
    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fallback-uoft", action="store_true",
                        help="If the City portal is unavailable, use archived 2025 TTC data.")
    args = parser.parse_args()
    meta = save_real_csv(args.out, fallback_uoft=args.fallback_uoft)
    print(json.dumps(meta, indent=2))
