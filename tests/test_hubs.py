"""Hub and area mapping: every field placed, known relationships hold."""

import pandas as pd
import pytest

from pathlib import Path

D = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def m():
    return pd.read_csv(D / "fields.csv").set_index("field")


def test_every_field_has_hub_and_area(m):
    assert m.hub.notna().all()
    assert m.area_group.notna().all()


@pytest.mark.parametrize("field,hub", [
    ("MORVIN", "ÅSGARD"), ("MIKKEL", "ÅSGARD"), ("TYRIHANS", "KRISTIN"), ("SYGNA", "STATFJORD"),
    ("VIGDIS", "SNORRE"), ("FRAM", "TROLL"), ("BØYLA", "ALVHEIM"), ("IVAR AASEN", "EDVARD GRIEG"),
    ("EMBLA", "ELDFISK"), ("HOD", "VALHALL"),
])
def test_known_tiebacks(m, field, hub):
    assert m.loc[field, "hub"] == hub


@pytest.mark.parametrize("field,area", [
    ("STATFJORD", "Tampen"), ("GULLFAKS", "Tampen"), ("EKOFISK", "Greater Ekofisk"),
    ("JOHAN SVERDRUP", "Utsira High"), ("TROLL", "Oseberg–Troll"), ("FRIGG", "Frigg–Alvheim–Balder"),
    ("HUGIN", "Yggdrasil"), ("ÅSGARD", "Haltenbanken"), ("SNØHVIT", "Hammerfest Basin"), ("VALHALL", "Southern North Sea"),
])
def test_known_areas(m, field, area):
    assert m.loc[field, "area_group"] == area


def test_tied_fields_share_their_hubs_area(m):
    tied = m[m.hub != m.index]
    for f, r in tied.iterrows():
        assert r.area_group == m.loc[r.hub, "area_group"], f
