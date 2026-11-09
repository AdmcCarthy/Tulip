"""Build data/seas.json: Relief's three map views of the shelf (North Sea, Norwegian Sea, Barents Sea), each with the Sodir
quadrants that held reserves and the maritime boundaries, in that view's own projection.

    uv run --group pipeline python scripts/build_seas.py <Relief dir>

Each view is a Relief region at its overview level of detail (`uv run python scripts/fetch_data.py` in Relief fetches the release),
drawn as Relief frames it: in the region's own projected coordinates (North Sea ETRS89 / UTM 32N, Norwegian Sea Lambert conic,
Barents Sea Lambert azimuthal), so the maps carry no rotation and no join between regions. Coordinates are written in units of
100 m from the region's south-west corner (x east, y north), which keeps the file small; the page scales them.

A quadrant belongs to the sea Sodir names for its fields: south of 62 N the North Sea, 62 to 70 N the Norwegian Sea, north of 70 N
the Barents Sea (tests/test_seas.py checks the rule against Sodir's own sea for all 139 fields). Quadrant values come from
data/quadrants_remaining.geojson, borders from data/borders.geojson (both built by scripts/build_data.py).

Each relief feature carries `k` (land or sea), `mid` (m, depth below or height above sea level at the mid-point of its band, which
sets its colour) and `g` (geometry). Paint sea features then land, each in ascending `mid`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import shapely
from pyproj import CRS, Transformer
from shapely.geometry import box, mapping, shape

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
UNIT = 100  # metres per coordinate unit
YEARS = ["1975", "1985", "1995", "2005", "2015", "2025"]
SEAS = [("north_sea", "North Sea"), ("norwegian_sea", "Norwegian Sea"), ("barents_sea", "Barents Sea")]
ATTRIBUTION = (
    "Base maps: Relief (github.com/AdmcCarthy/Relief), Copernicus DEM GLO-90 © DLR e.V. 2010-2014 and © Airbus 2014-2018, "
    "provided under COPERNICUS by the European Union and ESA; EMODnet Bathymetry Consortium (2024), EMODnet Digital Bathymetry (DTM); "
    "east of 43°E (the Barents Sea map), NOAA NCEI (2022), ETOPO 2022 15 Arc-Second Global Relief Model."
)


def sea_of(lat: float) -> str:
    """The sea Sodir assigns by latitude: North Sea below 62 N, Norwegian Sea to 70 N, Barents Sea above."""
    return "north_sea" if lat < 62 else "norwegian_sea" if lat < 70 else "barents_sea"


def _region(relief: Path, rid: str) -> dict:
    regions = json.loads((relief / "regions" / "regions.json").read_text(encoding="utf-8"))["regions"]
    return next(r for r in regions if r["id"] == rid)


def _mids(levels: list[float]) -> list[float]:
    """Mid-point of each stacked level to the next; the last band is as wide as the one before."""
    return [(v + levels[i + 1]) / 2 if i + 1 < len(levels) else v + (v - levels[i - 1]) / 2 for i, v in enumerate(levels)]


def _units(r: dict):
    """Region coordinates (m) to units from its south-west corner."""
    x0, y0 = r["extent"][0], r["extent"][1]
    return lambda g: shapely.transform(g, lambda c: np.column_stack([(c[:, 0] - x0) / UNIT, (c[:, 1] - y0) / UNIT]))


def _lonlat_to_units(r: dict):
    c = r["crs"]
    t = Transformer.from_crs("EPSG:4326", CRS.from_user_input(c.get("proj4") or c["code"]), always_xy=True)
    u = _units(r)
    return lambda g: u(shapely.transform(g, lambda p: np.column_stack(t.transform(p[:, 0], p[:, 1]))))


def relief_features(relief: Path, r: dict) -> list[dict]:
    geo = json.loads((relief / "data" / "out" / r["id"] / "overview.geojson").read_text(encoding="utf-8"))
    to_units = _units(r)
    mids = {}
    for kind in ("land", "sea"):
        sign = -1 if kind == "sea" else 1  # work in depth for the sea so both kinds run from 0 outwards
        lv = sorted({sign * ft["properties"]["level"] for ft in geo["features"] if ft["properties"]["kind"] == kind})
        mids[kind] = dict(zip(lv, _mids(lv), strict=True))
    out = []
    for ft in geo["features"]:
        p = ft["properties"]
        g = shapely.make_valid(to_units(shape(ft["geometry"])))
        g = shapely.set_precision(g.simplify(4), 1)  # 400 m tolerance on a 2 km cell, to whole units
        if g.is_empty:
            continue
        out.append({"k": p["kind"], "mid": mids[p["kind"]][(-1 if p["kind"] == "sea" else 1) * p["level"]], "g": mapping(g)})
    return sorted(out, key=lambda f: (f["k"] != "sea", f["mid"]))


def build(relief: Path) -> dict:
    quads = json.loads((D / "quadrants_remaining.geojson").read_text(encoding="utf-8"))["features"]
    used = [f for f in quads if any((f["properties"].get(y) or 0) > 0 for y in YEARS)]
    borders = json.loads((D / "borders.geojson").read_text(encoding="utf-8"))["features"]
    seas = []
    for rid, name in SEAS:
        r = _region(relief, rid)
        w, h = (r["extent"][2] - r["extent"][0]) / UNIT, (r["extent"][3] - r["extent"][1]) / UNIT
        frame, to_units = box(0, 0, w, h), _lonlat_to_units(r)
        qs = []
        for f in used:
            geom = shape(f["geometry"])
            if sea_of(geom.centroid.y) != rid:
                continue
            g = to_units(geom.segmentize(0.05))
            assert frame.contains(g), (rid, f["properties"]["q"])
            qs.append({"q": f["properties"]["q"], "v": [round(f["properties"].get(y) or 0, 2) for y in YEARS], "g": mapping(shapely.set_precision(g, 0.1))})
        lines = []
        for f in borders:
            g = shapely.set_precision(to_units(shape(f["geometry"]).segmentize(0.05)).intersection(frame).simplify(0.5), 0.1)
            if not g.is_empty:
                lines.append(mapping(g))
        # where north points on this view, at the middle of the quadrants drawn (degrees clockwise from up the page)
        mid = shapely.unary_union([shape(f["geometry"]) for f in used if sea_of(shape(f["geometry"]).centroid.y) == rid]).centroid
        a, b = to_units(mid), to_units(shapely.Point(mid.x, mid.y + 0.01))
        north = round(float(np.degrees(np.arctan2(b.x - a.x, b.y - a.y))), 1)
        seas.append({
            "id": rid, "name": name, "w": round(w), "h": round(h), "cell_m": r["lods"]["overview"]["cell"], "north_deg": north,
            "relief": relief_features(relief, r), "quads": sorted(qs, key=lambda q: q["q"]), "borders": lines,
        })
        print(f"{rid}: {len(seas[-1]['relief'])} relief features, {len(qs)} quadrants, {len(lines)} border lines")
    return {"unit_m": UNIT, "years": YEARS, "attribution": ATTRIBUTION, "seas": seas}


if __name__ == "__main__":
    rec = build(Path(sys.argv[1]))
    p = D / "seas.json"
    p.write_text(json.dumps(rec, separators=(",", ":")), encoding="utf-8")
    print(f"seas.json: {p.stat().st_size / 1024:.0f} kB")
