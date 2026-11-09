"""The sea maps: Relief's three map views, each with its quadrants, in one file the page draws from."""

import json
from pathlib import Path

import pandas as pd
import pytest
from shapely.geometry import box, shape
from shapely.ops import unary_union

D = Path(__file__).resolve().parents[1] / "data"
YEARS = ["1975", "1985", "1995", "2005", "2015", "2025"]


@pytest.fixture(scope="module")
def seas():
    return json.loads((D / "seas.json").read_text(encoding="utf-8"))


def test_three_views_in_order_with_the_stated_detail(seas):
    assert [s["id"] for s in seas["seas"]] == ["north_sea", "norwegian_sea", "barents_sea"]
    assert [s["cell_m"] for s in seas["seas"]] == [2000, 2000, 4000]  # the page's note: a 2 km cell, 4 km for the Barents Sea
    assert seas["years"] == YEARS and seas["unit_m"] == 100


def test_credits_name_every_source_the_maps_use(seas):
    a = seas["attribution"]
    assert all(k in a for k in ("Relief", "Copernicus", "EMODnet", "ETOPO"))
    assert "GEBCO" not in a  # the Atlantic fill belonged to the replaced map


def test_relief_is_painted_in_order_and_fills_every_frame(seas):
    for s in seas["seas"]:
        kinds = [f["k"] for f in s["relief"]]
        assert set(kinds) == {"land", "sea"} and kinds == sorted(kinds, key=lambda k: k != "sea")
        for kind in ("sea", "land"):
            mids = [f["mid"] for f in s["relief"] if f["k"] == kind]
            assert mids == sorted(mids) and mids[0] > 0
        frame = box(0, 0, s["w"], s["h"])
        shallow = unary_union([shape(f["g"]).buffer(0) for f in s["relief"] if f["mid"] == min(g["mid"] for g in s["relief"] if g["k"] == f["k"])])
        assert frame.intersection(shallow).area / frame.area > 0.97, s["id"]  # land and sea together leave no flat patch


def test_every_quadrant_with_reserves_is_in_exactly_one_sea_with_its_values(seas):
    quads = json.loads((D / "quadrants_remaining.geojson").read_text(encoding="utf-8"))["features"]
    used = {f["properties"]["q"]: f["properties"] for f in quads if any((f["properties"].get(y) or 0) > 0 for y in YEARS)}
    placed = [(s["id"], q) for s in seas["seas"] for q in s["quads"]]
    assert sorted(q["q"] for _, q in placed) == sorted(used)  # none dropped, none twice
    assert [sum(1 for sid, _ in placed if sid == k) for k in ("north_sea", "norwegian_sea", "barents_sea")] == [17, 8, 3]
    for sid, q in placed:
        assert q["v"] == pytest.approx([round(used[q["q"]].get(y) or 0, 2) for y in YEARS])
    for s in seas["seas"]:
        frame = box(0, 0, s["w"], s["h"])
        assert all(frame.contains(shape(q["g"])) for q in s["quads"]), s["id"]


def test_the_latitude_rule_is_sodirs_own_sea_for_every_field():
    f = pd.read_csv(D / "fields.csv").dropna(subset=["lat"])
    rule = f.lat.map(lambda lat: "North sea" if lat < 62 else "Norwegian sea" if lat < 70 else "Barents sea")
    assert len(f) == 139 and (rule == f.area).all()


def test_north_arrows_are_a_few_degrees_off(seas):
    for s in seas["seas"]:
        assert -15 < s["north_deg"] < 15, s["id"]  # "north is a few degrees off up the page"
    assert len({s["north_deg"] for s in seas["seas"]}) == 3  # and differs between the columns


def test_the_file_stays_small(seas):
    assert (D / "seas.json").stat().st_size < 600 * 1024
