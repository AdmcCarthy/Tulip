"""The Relief base map: lon/lat, ordered for painting, and covering the quadrants that ever held reserves."""

import json
from pathlib import Path

from shapely.geometry import shape

D = Path(__file__).resolve().parents[1] / "data"


def test_base_is_lonlat_and_painted_in_order():
    base = json.loads((D / "relief_shelf.json").read_text(encoding="utf-8"))
    assert base["crs"] == "EPSG:4326" and "Copernicus" in base["attribution"] and "EMODnet" in base["attribution"]
    assert "GEBCO" in base["attribution"]  # the Atlantic fill: its credit must travel with the base
    kinds = [f["properties"]["kind"] for f in base["features"]]
    assert set(kinds) == {"land", "sea"} and kinds == sorted(kinds, key=lambda k: k != "sea")
    for kind in ("sea", "land"):
        mids = [f["properties"]["mid"] for f in base["features"] if f["properties"]["kind"] == kind]
        assert mids == sorted(mids) and mids[0] > 0


def test_base_joins_all_five_regions_and_leaves_no_flat_patch():
    base = json.loads((D / "relief_shelf.json").read_text(encoding="utf-8"))
    assert base["regions"] == ["north_sea", "norwegian_sea", "barents_sea", "ne_europe", "atlantic"]
    assert {f["properties"]["region"] for f in base["features"]} == set(base["regions"])
    cover = shape(base["coverage"])
    # the places that showed a flat tint before: south and east Sweden, Finland, Denmark, the UK west of 3 W, the Baltic
    for lon, lat in ((16.0, 58.0), (25.0, 62.0), (10.0, 56.0), (-4.0, 56.5), (19.0, 57.5)):
        pt = shape({"type": "Point", "coordinates": [lon, lat]})
        assert cover.contains(pt), (lon, lat)
        assert any(shape(f["geometry"]).contains(pt) for f in base["features"]), (lon, lat)


def test_base_covers_the_quadrants_with_reserves():
    cover = shape(json.loads((D / "relief_shelf.json").read_text(encoding="utf-8"))["coverage"])
    quads = json.loads((D / "quadrants_remaining.geojson").read_text(encoding="utf-8"))["features"]
    used = [f for f in quads if any((f["properties"].get(y) or 0) > 0 for y in ("1975", "1985", "1995", "2005", "2015", "2025"))]
    assert used and all(cover.contains(shape(f["geometry"]).centroid) for f in used)
