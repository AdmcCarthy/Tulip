"""Tulip: datasets for the figures and every number the prose quotes.

Volumes are in Sm³ o.e. (SubScout's `volume` filter converts to boe for the reader); shares are 0–1.
Data come from scripts/build_data.py (Sodir FactPages and FactMaps; see data/README.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from subscout import metric

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
import hubs  # noqa: E402

M = 1e6  # MSm³ -> Sm³
# Field size classes: log scale in half-decade steps anchored on giant (500 MMboe) and super-giant (5 Bboe).
BOUNDS_MMBOE = [50, 160, 500, 1600, 5000]
CLASSES = [
    {"idx": 0, "short": "Small", "range": "< 50", "family": 0},
    {"idx": 1, "short": "Medium", "range": "50–160", "family": 0},
    {"idx": 2, "short": "Large", "range": "160–500", "family": 0},
    {"idx": 3, "short": "Giant", "range": "500–1,600", "family": 1},
    {"idx": 4, "short": "Giant", "range": "1,600–5,000", "family": 1},
    {"idx": 5, "short": "Super-giant", "range": "≥ 5,000", "family": 1},
]
ROOTED = ["EKOFISK", "FRIGG", "STATFJORD", "GULLFAKS", "TROLL", "ORMEN LANGE", "JOHAN SVERDRUP"]


def size_class(msm3_oe: float) -> int:
    mmboe = msm3_oe * 6.29
    return next((i for i, b in enumerate(BOUNDS_MMBOE) if mmboe < b), len(BOUNDS_MMBOE))


def _totals(d) -> pd.DataFrame:
    t = d["totals"].copy()
    t["date"] = pd.to_datetime(t["date"])
    t = t.set_index("date")
    t["liq"] = t.oil + t.liquids  # NGL and condensate grouped with oil
    return t


def _small(d) -> dict:
    """The shelf outside its giants (fields below 500 MMboe), quarter by quarter, in MSm³ o.e.

    Remaining volumes are summed per quarter for the giants and the rest. A field is added in the quarter it
    enters its stream (production start, or approval for the fields not yet producing), at its remaining
    volume then. What is produced follows from the books: added minus the change in what is left.
    """
    s, f = d["streams"], d["fields"].set_index("field")
    dates = s["dates"]
    yr = np.array([int(x[:4]) for x in dates])
    sub, big, adds = np.zeros(len(dates)), np.zeros(len(dates)), []
    by_cls, n_cls = np.zeros((3, len(dates))), [0, 0, 0]  # small, medium, large: remaining by quarter, and fields
    for x in s["fields"]:
        r = f.loc[x["key"]]
        tot = np.array(x["v"]["oil"]) + np.array(x["v"]["liquids"]) + np.array(x["v"]["gas"])
        c = size_class(r.recoverable_oil + r.recoverable_liquids + r.recoverable_gas)
        if c >= 3:
            big += tot
            continue
        n_cls[c] += 1
        by_cls[c] += tot
        if not tot.any():  # a field with no stream of its own (Troll Brent B, Hugin satellites): nothing to add
            continue
        sub += tot
        e = int(np.argmax(tot > 0))
        adds.append({"key": x["key"], "year": int(yr[e]), "vol": float(tot[e]), "producing": not bool(r.not_yet_producing)})
    return {"dates": dates, "yr": yr, "sub": sub, "big": big, "adds": adds, "by_cls": by_cls, "n_cls": n_cls}


def _end(sm: dict, year: int) -> float:
    """Remaining outside the giants at the last quarter of a year."""
    return float(sm["sub"][np.where(sm["yr"] == year)[0][-1]])


def _flows(sm: dict, y0: int, y1: int) -> tuple[float, float, float]:
    """Added, added by fields already producing, and produced, y0 to y1 inclusive, outside the giants."""
    inside = [a for a in sm["adds"] if y0 <= a["year"] <= y1]
    added = sum(a["vol"] for a in inside)
    return added, sum(a["vol"] for a in inside if a["producing"]), added - (_end(sm, y1) - _end(sm, y0 - 1))


def datasets(d):
    s, f = d["streams"], d["fields"].set_index("field")
    rows = []
    for x in s["fields"]:
        r = f.loc[x["key"]]
        liq = [round(a + b, 2) for a, b in zip(x["v"]["oil"], x["v"]["liquids"], strict=True)]
        gas = [round(v, 2) for v in x["v"]["gas"]]
        tot = [a + b for a, b in zip(liq, gas, strict=True)]
        rl, rg = r.recoverable_oil + r.recoverable_liquids, r.recoverable_gas
        rows.append({
            "key": x["key"], "name": x["key"].title(),
            "sea": x["area"].replace(" sea", " Sea"), "area": r.area_group, "hub": r.hub,
            "discovered": x["discovered"], "first_prod": x["first_prod"], "status": x["status"],
            "cross_border": x["cross_border"], "liq": liq, "gas": gas,
            "entry": next((i for i, v in enumerate(tot) if v > 0), len(tot) - 1),
            "cls": size_class(rl + rg), "dom": "gas" if rg > rl else "liq",
            "rec_liq": round(float(rl), 1), "rec_gas": round(float(rg), 1),
        })
    pot = d["potential"]["resource_accounts"]
    t = _totals(d)
    fp = f["first_production"].astype(str).str[:7]

    def jump(day: str) -> float:
        x = pd.Timestamp(day + "-01")
        return round(float(t.oe.loc[x] - t.oe.loc[x - pd.DateOffset(months=1)]), 1)

    lead = t.gas > t.liq
    gas_lead = next(x for x in lead.index if lead.loc[x:].all())
    events = [  # timeline annotations for the full-screen view; dates and values from the data
        {"date": fp["EKOFISK"], "year": fp["EKOFISK"][:4], "text": "First oil: Ekofisk"},
        {"date": fp["STATFJORD"], "year": fp["STATFJORD"][:4], "text": "Statfjord on stream"},
        {"date": fp["OSEBERG"], "year": f'{fp["GULLFAKS"][:4]}–{fp["OSEBERG"][2:4]}', "text": "Gullfaks and Oseberg"},
        {"date": fp["TROLL"], "year": fp["TROLL"][:4], "text": "Troll adds", "msm3": jump(fp["TROLL"])},
        {"date": f"{t.oe.idxmax():%Y-%m}", "year": f"{t.oe.idxmax():%Y}", "text": "Peak:", "msm3": round(float(t.oe.max()), 1), "after": "left"},
        {"date": f"{gas_lead:%Y-%m}", "year": f"{gas_lead:%Y}", "text": "Gas outweighs oil and liquids from here"},
        {"date": fp["ORMEN LANGE"], "year": fp["ORMEN LANGE"][:4], "text": "Ormen Lange and Snøhvit: the move north"},
        {"date": fp["JOHAN SVERDRUP"], "year": fp["JOHAN SVERDRUP"][:4], "text": "Johan Sverdrup adds", "msm3": jump(fp["JOHAN SVERDRUP"])},
    ]
    bulb = {
        "dates": s["dates"], "fields": rows, "classes": CLASSES, "axis_start": 1966,
        "axis_end": int(s["dates"][-1][:4]) + 10, "smooth_sigma": 3,
        "pending": pot["contingent_fields"] + pot["contingent_discoveries"],
        "rooted": ROOTED, "hub_names": hubs.HUB_NAMES,
        "peak": round(float(_totals(d).oe.max()), 1),
        "events": events, "now": round(float(t.oe.iloc[-1]), 1),
    }
    h = d["hindsight"]
    hind = pd.concat([
        pd.DataFrame({"year": h.year, "series": "Estimated at the time", "value": h.estimated_then}),
        pd.DataFrame({"year": h.year, "series": "Known now", "value": h.known_now}),
    ])
    sm = _small(d)
    cum = []
    for y in range(2005, 2026):  # since the end of 2004, outside the giants, cumulative
        added, on_stream, produced = _flows(sm, 2005, y)
        cum += [{"year": y, "series": "Added, approved or on stream", "value": added},
                {"year": y, "series": "Added, on stream", "value": on_stream},
                {"year": y, "series": "Produced", "value": produced}]
    return {"bulb": bulb, "hind": hind, "small_flows": pd.DataFrame(cum)}


def metrics(d):
    t = _totals(d)
    f = d["fields"].set_index("field")
    h = d["hindsight"].set_index("year")
    pot = d["potential"]["resource_accounts"]
    now = t.index[-1]
    pk = t.oe.idxmax()
    rec = f.recoverable_oe
    cls = rec.map(size_class)
    giants = cls >= 3

    def jump(day: str) -> float:
        x = pd.Timestamp(day)
        return float(t.oe.loc[x] - t.oe.loc[x - pd.DateOffset(months=1)])

    last12 = d["potential"]["prod_last12"]
    north_now = f.loc[f.area != "North sea", "remaining_oe"].sum() / f.remaining_oe.sum()
    snap = d["snap"]
    s95 = snap[snap.year == 1995]
    north_95 = s95[s95.lat > 62].remaining_oe.sum() / s95.remaining_oe.sum()
    tied = (f.hub != f.index).sum()
    n_hubs = (f.hub.value_counts() > 1).sum()
    sm = _small(d)
    sub, big = sm["sub"], sm["big"]
    ipk = int(np.argmax(sub + big))
    a0514, on0514, p0514 = _flows(sm, 2005, 2014)
    a1525, on1525, p1525 = _flows(sm, 2015, 2025)
    mid = (sm["yr"] >= 2000) & (sm["yr"] <= 2014)
    small_med = sm["by_cls"][0] + sm["by_cls"][1]  # classes small and medium: under 160 MMboe
    ipk_sm = int(np.argmax(small_med))
    sanct = [a for a in sm["adds"] if not a["producing"] and 2015 <= a["year"] <= 2025]
    m = metric
    fp = "sodir"
    return {
        "sub_at_peak": m(sub[ipk] * M, f"Remaining outside the giants at the quarter the shelf total peaks ({sm['dates'][ipk]}), Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "sub_share_peak": m(sub[ipk] / (sub[ipk] + big[ipk]), "Share of remaining reserves outside the giants at the shelf peak", fp, "derived"),
        "sub_now": m(sub[-1] * M, f"Remaining outside the giants, {sm['dates'][-1]}, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "sub_share_now": m(sub[-1] / (sub[-1] + big[-1]), "Share of remaining reserves outside the giants today", fp, "derived"),
        "n_small": m(sm["n_cls"][0], "Small fields (under 50 MMboe recoverable)", fp, "derived"),
        "n_medium": m(sm["n_cls"][1], "Medium fields (50 to 160 MMboe recoverable)", fp, "derived"),
        "n_large": m(sm["n_cls"][2], "Large fields (160 to 500 MMboe recoverable)", fp, "derived"),
        "large_share_sub": m(sm["by_cls"][2][-1] / sub[-1], "Share of what is left outside the giants that sits in large fields, today", fp, "derived"),
        "small_now": m(sm["by_cls"][0][-1] * M, f"Remaining in small fields, {sm['dates'][-1]}, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "medium_now": m(sm["by_cls"][1][-1] * M, f"Remaining in medium fields, {sm['dates'][-1]}, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "sm_now": m(small_med[-1] * M, f"Remaining in small and medium fields together, {sm['dates'][-1]}, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "sm_share_now": m(small_med[-1] / (sub[-1] + big[-1]), "Share of remaining reserves held by small and medium fields today", fp, "derived"),
        "sm_lo_0014": m(small_med[mid].min() * M, "Lowest remaining in small and medium fields, 2000 to 2014, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "sm_hi_0014": m(small_med[mid].max() * M, "Highest remaining in small and medium fields, 2000 to 2014, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "sm_peak": m(small_med[ipk_sm] * M, f"Highest remaining in small and medium fields ({sm['dates'][ipk_sm]}), Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "giants_fall": m((big[ipk] - big[-1]) * M, "Fall in the giants' remaining volume from the shelf peak to today, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "sub_rise": m((sub[-1] - sub[ipk]) * M, "Rise outside the giants from the shelf peak to today, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "offset_share": m((sub[-1] - sub[ipk]) / (big[ipk] - big[-1]), "Rise outside the giants as a share of the giants' fall since the shelf peak", fp, "derived"),
        "n_start_0514": m(sum(1 for a in sm["adds"] if 2005 <= a["year"] <= 2014), "Fields outside the giants entering their stream 2005 to 2014", fp, "derived"),
        "n_start_1525": m(sum(1 for a in sm["adds"] if 2015 <= a["year"] <= 2025), "Fields outside the giants entering their stream 2015 to 2025", fp, "derived"),
        "added_0514": m(a0514 * M, "Added outside the giants 2005 to 2014, volume left at entry, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "produced_0514": m(p0514 * M, "Produced outside the giants 2005 to 2014 (added minus the change in what is left), Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "added_1525": m(a1525 * M, "Added outside the giants 2015 to 2025, volume left at entry, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "produced_1525": m(p1525 * M, "Produced outside the giants 2015 to 2025 (added minus the change in what is left), Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "n_sanct_1525": m(len(sanct), "Fields outside the giants approved 2015 to 2025 and not yet producing", fp, "observed"),
        "sanct_1525": m(sum(a["vol"] for a in sanct) * M, "Volume in those fields, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "onstream_1525": m(on1525 * M, "Added outside the giants 2015 to 2025 by fields already producing, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
    } | {
        "n_fields": m(len(f), "Fields and field groups in the stack (Sleipner Øst, Vest and Gungne as one)", fp, "observed"),
        "peak_total": m(t.oe.max() * M, f"Highest monthly total of remaining reserves ({pk:%B %Y}), Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "now_total": m(t.oe.iloc[-1] * M, f"Remaining reserves, {now:%B %Y}, Sm³ o.e.", fp, "derived", "Sm³ o.e."),
        "fall_since_peak": m(1 - t.oe.iloc[-1] / t.oe.max(), "Fall in remaining reserves from the peak to today", fp, "derived"),
        "gas_share_now": m(t.gas.iloc[-1] / t.oe.iloc[-1], f"Gas share of remaining reserves, {now:%B %Y}", fp, "derived"),
        "gas_share_1980": m(t.loc["1980-12-01", "gas"] / t.loc["1980-12-01", "oe"], "Gas share of remaining reserves, December 1980", fp, "derived"),
        "ekofisk_rec": m(rec["EKOFISK"] * M, "Ekofisk recoverable volume, Sodir estimate 31.12.2025", fp, "observed", "Sm³ o.e."),
        "n_giants": m(int(giants.sum()), "Fields of 500 MMboe or more", fp, "derived"),
        "giant_share": m(rec[giants].sum() / rec.sum(), "Share of all recoverable volume held by giants", fp, "derived"),
        "top10_share": m(rec.nlargest(10).sum() / rec.sum(), "Share of all recoverable volume held by the ten largest fields", fp, "derived"),
        "troll_jump": m(jump("1995-09-01") * M, "Rise in total remaining reserves in September 1995, when Troll came on stream", fp, "derived", "Sm³ o.e."),
        "troll_rec": m(rec["TROLL"] * M, "Troll recoverable volume", fp, "observed", "Sm³ o.e."),
        "n_sub_giant": m(int((~giants).sum()), "Fields below 500 MMboe", fp, "derived"),
        "sub_giant_share": m(rec[~giants].sum() / rec.sum(), "Share of recoverable volume in fields below giant size", fp, "derived"),
        "sverdrup_jump": m(jump("2019-10-01") * M, "Rise in total remaining reserves in October 2019, when Johan Sverdrup came on stream", fp, "derived", "Sm³ o.e."),
        "then_2004": m(h.loc[2004, "estimated_then"] * M, "Remaining reserves in Sodir's 2004 field table", fp, "observed", "Sm³ o.e."),
        "known_2004": m(h.loc[2004, "known_now"] * M, "Same fields: today's remaining plus production 2005–2025", fp, "derived", "Sm³ o.e."),
        "n_fields_2004": m(int(h.loc[2004, "n_fields"]), "Fields in Sodir's 2004 reserve table", fp, "observed"),
        "growth_2004": m(h.loc[2004, "known_now"] / h.loc[2004, "estimated_then"] - 1, "Hindsight growth: known now over estimated in 2004, minus one", fp, "derived"),
        "north_share_now": m(north_now, "Share of remaining reserves in the Norwegian and Barents Seas today", fp, "derived"),
        "north_share_1995": m(north_95, "Share of remaining reserves north of 62°N, end of 1995", fp, "derived"),
        "n_tied": m(int(tied), "Fields produced through another field's facilities", fp, "interpreted"),
        "n_hubs": m(int(n_hubs), "Host fields with at least one tie-back", fp, "interpreted"),
        "big2_share": m(f.loc[["TROLL", "JOHAN SVERDRUP"], "remaining_oe"].sum() / f.remaining_oe.sum(), "Troll and Johan Sverdrup share of remaining reserves (31.12.2025)", fp, "derived"),
        "contingent": m((pot["contingent_fields"] + pot["contingent_discoveries"]) * M, "Contingent resources in fields and discoveries, Sodir resource accounts 31.12.2025", "ra", "observed", "Sm³ o.e."),
        "contingent_share": m((pot["contingent_fields"] + pot["contingent_discoveries"]) / f.remaining_oe.sum(), "Contingent resources (fields and discoveries) as a share of remaining reserves, both Sodir 31.12.2025", "ra", "derived"),
        "xb_max_gap": m(f.loc[f.cross_border, "balance_gap_oe"].abs().max() * M, "Largest mass-balance gap among cross-border fields (recoverable minus produced minus remaining)", fp, "derived", "Sm³ o.e."),
        "rp_years": m(t.oe.iloc[-1] / last12, f"Remaining reserves divided by production in the twelve months to {now:%B %Y}, years; assumes production holds at today's rate and no new reserves", fp, "interpreted"),
    }
