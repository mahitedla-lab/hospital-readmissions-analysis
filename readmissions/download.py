"""Download the two CMS Provider Data Catalog datasets used in the analysis.

    Hospital Readmissions Reduction Program   dataset id 9n3s-kdb3
    Hospital General Information              dataset id xubh-q36u

The CSV link in the catalog changes with every CMS release (it contains a hash), so the
current link is looked up from the catalog metadata API each time.
"""
from pathlib import Path
from urllib.parse import urlparse

import requests

DATASETS = {
    "hrrp.csv": "9n3s-kdb3",
    "hospital_general_information.csv": "xubh-q36u",
}
META_URL = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/{id}"
FALLBACK_URL = "https://data.cms.gov/provider-data/api/1/datastore/query/{id}/0/download?format=csv"


def resolve_csv_url(dataset_id: str) -> str:
    try:
        resp = requests.get(META_URL.format(id=dataset_id), timeout=60)
        resp.raise_for_status()
        urls = [d.get("downloadURL") for d in resp.json().get("distribution", []) if d.get("downloadURL")]
        official = [u for u in urls if urlparse(u).hostname == "data.cms.gov"]
        if official or urls:
            return (official or urls)[0]
    except (requests.RequestException, ValueError):
        pass
    return FALLBACK_URL.format(id=dataset_id)


def download_all(out_dir) -> dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for filename, dataset_id in DATASETS.items():
        url = resolve_csv_url(dataset_id)
        dest = out_dir / filename
        print(f"downloading {filename}\n  from {url}")
        with requests.get(url, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=1 << 20):
                    fh.write(chunk)
        print(f"  saved {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
        paths[filename] = dest
    return paths
