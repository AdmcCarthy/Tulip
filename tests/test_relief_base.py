"""The Relief base map: lon/lat, ordered for painting, and covering the quadrants that ever held reserves."""

import json
from pathlib import Path

from shapely.geometry import shape

D = Path(__file__).resolve().parents[1] / "data"


def test_base_is_lonlat_and_painted_in_order():
    base = json.loads((D / "relief_shelf.json").read_text(encoding="utf-8"))
    assert base["crs"] == "EPSG:4326" and "Copernicus" in base["attribution"] and "EMODnet" in base["attribution"]
    kinds = [f["properties"]["kind"] for f in base["features"]]
    assert set(kinds) == {"land", "sea"} and kinds == sorted(kinds, key=lambda k: k != "sea")
    for kind in ("sea", "land"):
        mids = [f["properties"]["mid"] for f in base["features"] if f["properties"]["kind"] == kind]
        assert mids == sorted(mids) and mids[0] > 0


def test_base_covers_the_quadrants_with_reserves():
    cover = shape(json.loads((D / "relief_shelf.json").read_text(encoding="utf-8"))["coverage"])
    quads = json.loads((D / "quadrants_remaining.geojson").read_text(encoding="utf-8"))["features"]
    used = [f for f in quads if any((f["properties"].get(y) or 0) > 0 for y in ("1975", "1985", "1995", "2005", "2015", "2025"))]
    assert used and all(cover.contains(shape(f["geometry"]).centroid) for f in used)
