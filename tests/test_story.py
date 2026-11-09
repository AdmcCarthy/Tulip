"""The story builds cleanly with SubScout, and the numbers it quotes match independent calculations."""

import json
from pathlib import Path

import pandas as pd
import pytest

from subscout.build import build

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("site")
    rep = build(ROOT, out)
    ledger = {r["name"]: r for r in json.loads((out / "build-report.json").read_text())["ledger"]}
    return rep, ledger, out


def test_builds_without_errors_or_warnings(built):
    rep, _, out = built
    assert rep.errors == [] and rep.warnings == []
    for m in ("bulb", "bulb_pair", "bulb_total", "pack", "cream", "maps", "common"):
        assert (out / "figures" / f"{m}.js").exists()


def _v(ledger, name):
    return float(ledger[name]["value"].replace(",", ""))


def test_peak_and_today(built):
    _, ledger, _ = built
    t = pd.read_csv(D / "totals_monthly.csv", parse_dates=["date"]).set_index("date")
    assert t.oe.idxmax().year == 2000  # the prose says the peak came early in 2000
    assert _v(ledger, "peak_total") == pytest.approx(t.oe.max() * 1e6, rel=1e-5)
    assert _v(ledger, "now_total") == pytest.approx(t.oe.iloc[-1] * 1e6, rel=1e-5)


def test_gas_has_led_liquids_since_end_2003():
    t = pd.read_csv(D / "totals_monthly.csv", parse_dates=["date"]).set_index("date")
    lead = t.gas > t.oil + t.liquids
    assert not lead.loc["2003-11-01"] and lead.loc["2003-12-01":].all()


def test_years_quoted_in_prose():
    f = pd.read_csv(D / "fields.csv").set_index("field")
    assert f.loc["EKOFISK", "discovery_year"] == 1969 and f.loc["EKOFISK", "first_production"].startswith("1971-06")
    assert f.loc["STATFJORD", "first_production"].startswith("1979")
    assert f.loc["SNORRE", "first_production"].startswith("1992")
    assert f.loc["TROLL", "discovery_year"] == 1979 and f.loc["TROLL", "first_production"].startswith("1995")
    assert f.loc["JOHAN SVERDRUP", "discovery_year"] == 2010 and f.loc["JOHAN SVERDRUP", "first_production"].startswith("2019-10")


def test_shares_and_counts(built):
    _, ledger, _ = built
    f = pd.read_csv(D / "fields.csv").set_index("field")
    rec = f.recoverable_oe
    giants = rec * 6.29 >= 500
    assert _v(ledger, "n_giants") == giants.sum()
    assert _v(ledger, "giant_share") == pytest.approx(rec[giants].sum() / rec.sum(), rel=1e-5)
    assert _v(ledger, "n_fields") == len(f)
    assert _v(ledger, "big2_share") == pytest.approx(f.loc[["TROLL", "JOHAN SVERDRUP"], "remaining_oe"].sum() / f.remaining_oe.sum(), rel=1e-5)


def test_hindsight(built):
    _, ledger, _ = built
    h = pd.read_csv(D / "hindsight.csv").set_index("year")
    assert _v(ledger, "growth_2004") == pytest.approx(h.loc[2004, "known_now"] / h.loc[2004, "estimated_then"] - 1, rel=1e-5)


def test_ekofisk_alone_until_1977_and_no_barents_production_by_2005():
    s = json.loads((D / "streams.json").read_text())
    d = s["dates"]
    live = lambda i: {f["key"] for f in s["fields"] if sum(f["v"][k][i] for k in f["v"]) > 0}
    assert live(d.index("1976-12")) == {"EKOFISK"}
    assert {"FRIGG", "COD", "VEST EKOFISK"} <= live(d.index("1977-12"))
    assert not {f["key"] for f in s["fields"] if f["area"] == "Barents sea"} & live(d.index("2005-12"))


def test_full_screen_view(built, tmp_path):
    import subprocess, sys
    _, _, out = built
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_full.py"), str(out)], check=True)
    page = (out / "full" / "index.html").read_text()
    assert "../figures/bulb_pair.js" in page and "poster" in page
    data = json.loads(page.split('id="data">')[1].split("</script>")[0])
    years = [e["year"] for e in data["bulb"]["events"]]
    assert years[0] == "1971" and "2000" in years and "2019" in years


def test_every_annual_table_understated_its_fields():
    """The prose says every annual table from 2004 to 2024 booked less than its fields turned out to hold."""
    h = pd.read_csv(D / "hindsight.csv").set_index("year")
    assert (h.loc[2004:2024, "known_now"] > h.loc[2004:2024, "estimated_then"]).all()
    assert h.loc[2025, "known_now"] == pytest.approx(h.loc[2025, "estimated_then"])  # equal by construction, so excluded


def test_contingent_share_matches_resource_accounts(built):
    _, ledger, _ = built
    pot = json.loads((D / "potential.json").read_text())["resource_accounts"]
    f = pd.read_csv(D / "fields.csv")
    want = (pot["contingent_fields"] + pot["contingent_discoveries"]) / f.remaining_oe.sum()
    assert float(ledger["contingent_share"]["value"]) == pytest.approx(want, abs=1e-5)
    assert 0.4 < want < 0.7  # the prose says "equal to" about half again
