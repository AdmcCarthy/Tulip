"""Fetch Sodir FactPages tables (CSV) and FactMaps layers (GeoJSON) used by Tulip.

Data: Sodir (Norwegian Offshore Directorate), Norwegian Licence for Open Government Data (NLOD 2.0).
Usage: python scripts/fetch_sodir.py [out_dir]   (default data/raw)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

FACTPAGES = (
    "https://factpages.sodir.no/public?/Factpages/external/tableview/{t}"
    "&rs:Command=Render&rc:Toolbar=false&rc:Parameters=f&IpAddress=not_used"
    "&CultureCode=en&rs:Format=CSV&Top100=false"
)
DATA = "https://factmaps.sodir.no/api/rest/services/DataService/Data/FeatureServer"
BASE = "https://factmaps.sodir.no/api/rest/services/Basemap/Basemap_simple_grey/MapServer"

TABLES = [
    "field",
    "field_reserves",
    "field_in_place_volumes",
    "field_production_monthly",
    "field_activity_status_hst",
    "field_description",
    "field_operator_hst",
    "discovery",
    "discovery_reserves",
]

LAYERS = {  # name: (url, where, fields, maxAllowableOffset)
    "fields.geojson": (f"{DATA}/7100", "1=1", "fldName,fldNpdidField,fldHcType,fldMainArea", 0.002),
    "quadrants.geojson": (f"{DATA}/1002", "1=1", "qadName", 0.002),
    "land.geojson": (f"{BASE}/5", "1=1", "*", 0.01),
    "sea_boundaries.geojson": (f"{BASE}/3", "1=1", "*", 0.005),
}


def get(url: str, **kw) -> requests.Response:
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=300, **kw)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("unreachable")


def layer(url: str, where: str, fields: str, offset: float | None) -> dict:
    feats, start = [], 0
    while True:
        p = {"where": where, "outFields": fields, "returnGeometry": "true", "outSR": 4326,
             "f": "geojson", "resultOffset": start, "resultRecordCount": 1000}
        if offset:
            p["maxAllowableOffset"] = offset
        d = get(f"{url}/query", params=p).json()
        if "error" in d:
            raise RuntimeError(f"{url}: {d['error']}")
        batch = d.get("features", [])
        feats += batch
        more = d.get("exceededTransferLimit") or d.get("properties", {}).get("exceededTransferLimit")
        if not batch or not more:
            return {"type": "FeatureCollection", "features": feats}
        start += len(batch)


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for t in TABLES:
        text = get(FACTPAGES.format(t=t)).content.decode("utf-8-sig")
        (out / f"{t}.csv").write_text(text, encoding="utf-8")
        print(f"{t}: {text.count(chr(10)) - 1} rows")
    for name, (url, where, fields, off) in LAYERS.items():
        fc = layer(url, where, fields, off)
        (out / name).write_text(json.dumps(fc), encoding="utf-8")
        print(f"{name}: {len(fc['features'])} features")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw"))
