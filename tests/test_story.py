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
    for m in ("bulb", "bulb_pair", "bulb_total", "bulb_trio", "bulb_trio_stretched", "pack", "cream", "maps", "common"):
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


def _outside_giants():
    """Remaining outside the giants by quarter, entries and production, straight from the raw files."""
    s = json.loads((D / "streams.json").read_text(encoding="utf-8"))
    f = pd.read_csv(D / "fields.csv").set_index("field")
    n = len(s["dates"])
    yr = [int(x[:4]) for x in s["dates"]]
    sub, big, ents, produced = [0.0] * n, [0.0] * n, [], {}
    cls, n_cls = [[0.0] * n for _ in range(3)], [0, 0, 0]  # small (under 50 MMboe), medium (50 to 160), large (160 to 500)
    for x in s["fields"]:
        tot = [a + b + c for a, b, c in zip(x["v"]["oil"], x["v"]["liquids"], x["v"]["gas"], strict=True)]
        r = f.loc[x["key"]]
        mmboe = (r.recoverable_oil + r.recoverable_liquids + r.recoverable_gas) * 6.29
        giant = mmboe >= 500
        c = 0 if mmboe < 50 else 1 if mmboe < 160 else 2
        for t, v in enumerate(tot):
            (big if giant else sub)[t] += v
            if not giant:
                cls[c][t] += v
        if not giant:
            n_cls[c] += 1
        if giant or not any(v > 0 for v in tot):
            continue
        e = next(t for t, v in enumerate(tot) if v > 0)
        ents.append({"key": x["key"], "year": yr[e], "vol": tot[e], "producing": not bool(r.not_yet_producing)})
        for t in range(e + 1, n):
            produced[yr[t]] = produced.get(yr[t], 0.0) + (tot[t - 1] - tot[t])
    return {"dates": s["dates"], "yr": yr, "sub": sub, "big": big, "ents": ents, "produced": produced, "cls": cls, "n_cls": n_cls}


def _m(ledger, name):
    return float(ledger[name]["value"].replace(",", ""))


def test_outside_the_giants_volumes(built):
    _, ledger, _ = built
    g = _outside_giants()
    sub, big = g["sub"], g["big"]
    ipk = max(range(len(sub)), key=lambda i: sub[i] + big[i])
    assert g["dates"][ipk].startswith("2000")  # the prose says the shelf peaked in 2000
    assert _m(ledger, "sub_at_peak") == pytest.approx(sub[ipk] * 1e6, rel=1e-5)
    assert _m(ledger, "sub_share_peak") == pytest.approx(sub[ipk] / (sub[ipk] + big[ipk]), rel=1e-5)
    assert _m(ledger, "sub_now") == pytest.approx(sub[-1] * 1e6, rel=1e-5)
    assert _m(ledger, "sub_share_now") == pytest.approx(sub[-1] / (sub[-1] + big[-1]), rel=1e-5)


def test_small_and_medium_fields(built):
    """The three figures and the prose after them: small (under 50 MMboe) and medium (50 to 160), large left out."""
    _, ledger, _ = built
    g = _outside_giants()
    small, medium, large = g["cls"]
    sm = [a + b for a, b in zip(small, medium, strict=True)]
    sub, big = g["sub"], g["big"]
    assert [_m(ledger, k) for k in ("n_small", "n_medium", "n_large")] == g["n_cls"]
    assert sum(g["n_cls"]) == 106  # "106 fields remain" outside the giants
    assert _m(ledger, "large_share_sub") == pytest.approx(large[-1] / sub[-1], rel=1e-5)
    for name, arr in (("small_now", small), ("medium_now", medium), ("sm_now", sm)):
        assert _m(ledger, name) == pytest.approx(arr[-1] * 1e6, rel=1e-5), name
    assert _m(ledger, "sm_share_now") == pytest.approx(sm[-1] / (sub[-1] + big[-1]), rel=1e-5)
    mid = [v for v, y in zip(sm, g["yr"], strict=True) if 2000 <= y <= 2014]
    assert _m(ledger, "sm_lo_0014") == pytest.approx(min(mid) * 1e6, rel=1e-5)
    assert _m(ledger, "sm_hi_0014") == pytest.approx(max(mid) * 1e6, rel=1e-5)
    # "rose to X at the end of 2023 and has eased since"
    ipeak = max(range(len(sm)), key=lambda i: sm[i])
    assert g["dates"][ipeak] == "2023-12" and sm[-1] < sm[ipeak]
    assert _m(ledger, "sm_peak") == pytest.approx(sm[ipeak] * 1e6, rel=1e-5)
    # "held level to 2014": the whole range 2000-2014 sits below the 2023 peak by a wide margin
    assert max(mid) < 0.7 * sm[ipeak]
    # "medium fields held more than small ones in every year from 2000" (checked every quarter)
    assert all(m > s for m, s, y in zip(medium, small, g["yr"], strict=True) if y >= 2000)
    # large fields are about half of what is left outside the giants, which is why they are named as left out
    assert 0.45 < large[-1] / sub[-1] < 0.55


def test_giants_fall_and_share(built):
    _, ledger, _ = built
    g = _outside_giants()
    sub, big = g["sub"], g["big"]
    ipk = max(range(len(sub)), key=lambda i: sub[i] + big[i])
    assert _m(ledger, "giants_fall") == pytest.approx((big[ipk] - big[-1]) * 1e6, rel=1e-5)
    assert _m(ledger, "sub_rise") == pytest.approx((sub[-1] - sub[ipk]) * 1e6, rel=1e-5)
    assert _m(ledger, "offset_share") == pytest.approx((sub[-1] - sub[ipk]) / (big[ipk] - big[-1]), rel=1e-5)
    # "most of the rise in their share comes from the giants' decline": hold the giants at their peak and less than half remains
    held = sub[-1] / (sub[-1] + big[ipk]) - sub[ipk] / (sub[ipk] + big[ipk])
    rise = sub[-1] / (sub[-1] + big[-1]) - sub[ipk] / (sub[ipk] + big[ipk])
    assert held < 0.5 * rise


def test_additions_and_production_outside_the_giants(built):
    _, ledger, _ = built
    g = _outside_giants()

    def window(y0, y1):
        inside = [e for e in g["ents"] if y0 <= e["year"] <= y1]
        return (len(inside), sum(e["vol"] for e in inside), sum(e["vol"] for e in inside if e["producing"]),
                sum(g["produced"].get(y, 0.0) for y in range(y0, y1 + 1)))

    n1, a1, on1, p1 = window(2005, 2014)
    n2, a2, on2, p2 = window(2015, 2025)
    assert _m(ledger, "n_start_0514") == n1 and _m(ledger, "n_start_1525") == n2
    for name, want in (("added_0514", a1), ("produced_0514", p1), ("added_1525", a2), ("produced_1525", p2), ("onstream_1525", on2)):
        assert _m(ledger, name) == pytest.approx(want * 1e6, rel=1e-5), name
    assert a2 > p2  # "a surplus on paper"
    assert on2 == pytest.approx(p2, rel=0.02)  # "close to what the whole group produced"


def test_sanctioned_but_not_producing():
    g = _outside_giants()
    sanct = [e for e in g["ents"] if not e["producing"] and 2015 <= e["year"] <= 2025]
    assert {e["year"] for e in sanct} == {2023, 2024}  # "approved in 2023 and 2024"
    assert {"MUNIN", "HUGIN"} <= {e["key"] for e in sanct}  # "among them Munin and Hugin"


def test_sanctioned_count_and_volume(built):
    _, ledger, _ = built
    g = _outside_giants()
    sanct = [e for e in g["ents"] if not e["producing"] and 2015 <= e["year"] <= 2025]
    assert _m(ledger, "n_sanct_1525") == len(sanct)
    assert _m(ledger, "sanct_1525") == pytest.approx(sum(e["vol"] for e in sanct) * 1e6, rel=1e-5)


def test_cumulative_additions_chart():
    g = _outside_giants()
    on = sum(e["vol"] for e in g["ents"] if 2005 <= e["year"] <= 2025 and e["producing"])
    produced = sum(g["produced"].get(y, 0.0) for y in range(2005, 2026))
    # the chart title says additions "have only kept pace": on-stream additions end below production, within 5%
    assert on < produced and on > 0.95 * produced
