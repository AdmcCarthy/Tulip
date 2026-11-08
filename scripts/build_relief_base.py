"""Build the Relief base map for the quadrant maps: data/relief_shelf.json.

    uv run --group pipeline python scripts/build_relief_base.py <Relief dir>

The base is Relief's stacked land and sea-floor polygons (Copernicus DEM GLO-90 and EMODnet Bathymetry), taken from a Relief
data release (`uv run python scripts/fetch_data.py` in Relief). Relief regions are projected, so each layer is converted to
longitude and latitude here, the frame the Sodir overlays (wells, fields, licences) already use; the maps project everything
together in the browser, so base and overlays cannot drift apart.

- relief_shelf.json: `north_sea`, `norwegian_sea` and `barents_sea` at their overview level (2 km cell; 4 km for the Barents Sea), joined without overlap
  (the finer region wins where two meet), for the shelf-wide map (the same base as Wildcat's shelf map). Relief has no single region over 56 to 74 N, so the join is
  clipped to the area the three regions cover; the maps clip the base to `coverage`.

Each feature carries `kind` (land or sea), `level` (m, the stack threshold; negative for sea) and `mid` (m, depth below or height above sea level at the mid-point
to the next level, which sets its colour). Paint land and sea features in ascending `mid` order.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import shapely
from pyproj import CRS, Transformer
from shapely.geometry import box, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data"
ATTRIBUTION = (
    "Base map: Relief (github.com/AdmcCarthy/Relief), Copernicus DEM GLO-90 © DLR e.V. 2010-2014 and © Airbus 2014-2018, "
    "provided under COPERNICUS by the European Union and ESA; EMODnet Bathymetry Consortium (2024), EMODnet Digital Bathymetry (DTM)."
)


def _region(relief: Path, rid: str) -> dict:
    regions = json.loads((relief / "regions" / "regions.json").read_text(encoding="utf-8"))["regions"]
    return next(r for r in regions if r["id"] == rid)


def _crs(r: dict) -> CRS:
    c = r["crs"]
    return CRS.from_user_input(c.get("proj4") or c["code"])


def _mids(levels: list[float]) -> list[float]:
    """Mid-point of each stacked level to the next; the last band is as wide as the one before."""
    return [(v + levels[i + 1]) / 2 if i + 1 < len(levels) else v + (v - levels[i - 1]) / 2 for i, v in enumerate(levels)]


def _to_lonlat(r: dict):
    t = Transformer.from_crs(_crs(r), "EPSG:4326", always_xy=True)
    return lambda geom: shapely.transform(geom, lambda c: np.column_stack(t.transform(c[:, 0], c[:, 1])))


def _extent_lonlat(r: dict):
    x0, y0, x1, y1 = r["extent"]
    return _to_lonlat(r)(box(x0, y0, x1, y1).segmentize(5_000))


def layers(relief: Path, rid: str, lod: str, frame, zone) -> list[dict]:
    """Features of one region and level of detail, in lon/lat, clipped to `zone` and the map frame."""
    r = _region(relief, rid)
    to = _to_lonlat(r)
    geo = json.loads((relief / "data" / "out" / rid / f"{lod}.geojson").read_text(encoding="utf-8"))
    mids = {}
    for kind in ("land", "sea"):
        # sea levels are negative heights: work in depth (m, positive down) so both kinds run from 0 outwards
        sign = -1 if kind == "sea" else 1
        lv = sorted({sign * ft["properties"]["level"] for ft in geo["features"] if ft["properties"]["kind"] == kind})
        mids[kind] = dict(zip(lv, _mids(lv), strict=True))
    clip = shapely.make_valid(zone).intersection(frame)
    out = []
    for ft in geo["features"]:
        p = ft["properties"]
        g = shapely.make_valid(to(shape(ft["geometry"]))).intersection(clip)
        g = shapely.set_precision(g.simplify(0.002), 0.001)
        if g.is_empty:
            continue
        out.append({"type": "Feature", "properties": {"kind": p["kind"], "level": p["level"], "mid": mids[p["kind"]][(-1 if p["kind"] == "sea" else 1) * p["level"]], "region": rid},
                    "geometry": mapping(g)})
    return out


def build(relief: Path, specs: list[tuple[str, str]], frame, name: str) -> None:
    taken = None
    feats: list[dict] = []
    for rid, lod in specs:  # finest region first: it wins where regions meet
        zone = _extent_lonlat(_region(relief, rid))
        own = zone if taken is None else zone.difference(taken)
        got = layers(relief, rid, lod, frame, own)
        feats += got
        taken = zone if taken is None else unary_union([taken, zone])
    coverage = shapely.set_precision(taken.intersection(frame).simplify(0.002), 0.001)
    rec = {
        "type": "FeatureCollection",
        "crs": "EPSG:4326",
        "regions": [rid for rid, _ in specs],
        "coverage": mapping(coverage),
        "attribution": ATTRIBUTION,
        "features": sorted(feats, key=lambda f: (f["properties"]["kind"] != "sea", f["properties"]["mid"])),
    }
    p = OUT / name
    p.write_text(json.dumps(rec, separators=(",", ":")), encoding="utf-8")
    print(f"{name}: {len(feats)} features, {p.stat().st_size / 1024:.0f} kB")


if __name__ == "__main__":
    relief = Path(sys.argv[1])
    build(relief, [("north_sea", "overview"), ("norwegian_sea", "overview"), ("barents_sea", "overview")], box(-2.0, 55.0, 42.0, 77.0), "relief_shelf.json")
