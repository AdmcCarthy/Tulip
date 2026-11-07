"""Checks on the built data: every number the page quotes rests on these."""

import json
from pathlib import Path

import pandas as pd
import pytest

D = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def fields():
    return pd.read_csv(D / "fields.csv")


def test_remaining_matches_sodir_resource_accounts(fields):
    ra = json.loads((D / "potential.json").read_text())["resource_accounts"]
    assert fields.remaining_oe.sum() == pytest.approx(ra["reserves"], abs=1)


def test_mass_balance_small_except_known(fields):
    # recoverable - produced - remaining; Troll carries ~21 MSm3 o.e. unexplained (1% of the field)
    gap = fields.set_index("field").balance_gap_oe.abs()
    assert gap.drop("TROLL").max() < 6
    assert gap["TROLL"] < 25


def test_cross_border_fields_balance(fields):
    xb = fields[fields.cross_border]
    assert len(xb) == 10
    assert xb.balance_gap_oe.abs().max() < 1


def test_shut_down_fields_taper_to_zero(fields):
    s = json.loads((D / "streams.json").read_text())
    for f in s["fields"]:
        if f["status"] == "Shut down":
            assert sum(v[-1] for v in f["v"].values()) < 0.05, f["key"]


def test_stream_today_equals_reserves_minus_2026_production():
    t = pd.read_csv(D / "totals_monthly.csv", parse_dates=["date"]).set_index("date")
    ra = json.loads((D / "potential.json").read_text())["resource_accounts"]
    dec = t.loc["2025-12-01", "oe"]
    # five fields started in 2026 and are not in the December 2025 stack
    assert ra["reserves"] - 40 < dec <= ra["reserves"]


def test_hindsight_meets_today():
    h = pd.read_csv(D / "hindsight.csv").set_index("year")
    assert h.loc[2025, "estimated_then"] == pytest.approx(h.loc[2025, "known_now"], abs=0.5)
    assert (h.known_now >= h.estimated_then - 80).all()
