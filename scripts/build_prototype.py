"""Fill prototype/template.html with Tulip's data -> prototype/index.html (first-pass review page).

Every number in the arc text is computed here from data/ (no typed figures).
Usage: python scripts/build_prototype.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"


def f0(v: float) -> str:
    return f"{v:,.0f}"


def pct(v: float) -> str:
    return f"{v:.0%}"


def main() -> None:
    streams = json.loads((D / "streams.json").read_text())
    pot = json.loads((D / "potential.json").read_text())
    m = pd.read_csv(D / "fields.csv", parse_dates=["first_production"])
    t = pd.read_csv(D / "totals_monthly.csv", parse_dates=["date"]).set_index("date")
    h = pd.read_csv(D / "hindsight.csv")
    fi = m.set_index("field")

    pk = t.oe.idxmax()
    now = t.index[-1]
    gas_cross = t[t.gas > t.oil].index.min()
    tot_rec = m.recoverable_oe.sum()
    small = m[m.recoverable_oe < 50]
    big2 = fi.loc[["TROLL", "JOHAN SVERDRUP"], "remaining_oe"].sum() / fi.remaining_oe.sum()
    h0 = h.iloc[0]

    def jump(date: str) -> float:
        d = pd.Timestamp(date)
        return float(t.oe.loc[d] - t.oe.loc[d - pd.DateOffset(months=1)])

    arc = [
        {"when": "1971", "date": "1971-06", "mark": "1971", "short": "Ekofisk on stream",
         "title": "The stem",
         "text": f"Ekofisk, found in 1969, starts production in June 1971 and is the whole bulb for "
                 f"years: {f0(fi.loc['EKOFISK','recoverable_oe'])} MSm³ o.e. by today's estimate."},
        {"when": "1979", "date": "1979-11", "mark": "1979", "short": "Statfjord",
         "title": "The giants arrive",
         "text": f"Statfjord ({f0(fi.loc['STATFJORD','recoverable_oe'])}, Norwegian share), then "
                 f"Gullfaks and Oseberg in 1986–88. The ten largest fields hold "
                 f"{pct(m.nlargest(10,'recoverable_oe').recoverable_oe.sum()/tot_rec)} of all the "
                 f"volume ever booked on the shelf."},
        {"when": "1995", "date": "1995-09", "mark": "1995", "short": "Troll",
         "title": "Gas at the heart",
         "text": f"Troll comes on stream and adds {f0(jump('1995-09-01'))} MSm³ o.e. to the bulb in a "
                 f"single month. Found in 1979, it is still the largest field by far: "
                 f"{f0(fi.loc['TROLL','recoverable_oe'])} recoverable, {f0(fi.loc['TROLL','remaining_oe'])} left."},
        {"when": f"{pk:%Y}", "date": f"{pk:%Y-%m}", "mark": f"{pk:%Y}", "short": "Peak",
         "title": "The widest point",
         "text": f"Remaining reserves peak at {f0(t.oe.max())} MSm³ o.e. in {pk:%B %Y}, "
                 f"about {t.oe.max()*6.29/1000:,.0f} billion boe. By {gas_cross:%B %Y} gas overtakes oil "
                 f"in what is left. It is {pct(t.loc[now,'gas']/t.loc[now,'oe'])} gas today."},
        {"when": "2007", "date": "2007-09", "mark": "2007", "short": "Ormen Lange, Snøhvit",
         "title": "Moving north",
         "text": f"Ormen Lange ({f0(fi.loc['ORMEN LANGE','recoverable_oe'])}) and Snøhvit "
                 f"({f0(fi.loc['SNØHVIT','recoverable_oe'])}) bring the Norwegian and Barents Seas into "
                 f"the bulb. Meanwhile the edges fill with small fields: {len(small)} of the "
                 f"{len(m)} hold under 50 MSm³ o.e. each, {pct(small.recoverable_oe.sum()/tot_rec)} of "
                 f"the total between them."},
        {"when": "2019", "date": "2019-10", "mark": "2019", "short": "Johan Sverdrup",
         "title": "A late bloom",
         "text": f"Johan Sverdrup, found in {int(fi.loc['JOHAN SVERDRUP','discovery_year'])} on the Utsira "
                 f"High in a long-explored part of the North Sea, adds {f0(jump('2019-10-01'))} MSm³ o.e. "
                 f"the month it starts. Exploration in a mature area can still change the shape."},
        {"when": f"{now:%Y}", "date": f"{now:%Y-%m}", "mark": "Today", "short": f"{f0(t.oe.iloc[-1])} left",
         "title": "The neck",
         "text": f"{f0(t.oe.iloc[-1])} MSm³ o.e. remain in {fmt_month(now)}. Troll and Johan Sverdrup "
                 f"hold {pct(big2)} of it. Below the line are the volumes not yet sanctioned "
                 f"({f0(pot['resource_accounts']['contingent_fields']+pot['resource_accounts']['contingent_discoveries'])}) "
                 f"and Sodir's expected undiscovered volume ({f0(pot['resource_accounts']['undiscovered'])})."},
        {"when": "Twist", "title": "Drawn with hindsight",
         "text": f"Every width above uses today's estimate. At the end of {int(h0.year)} Sodir's tables put "
                 f"{f0(h0.estimated_then)} MSm³ o.e. in the {int(h0.n_fields)} fields then booked; we now "
                 f"know they held {f0(h0.known_now)}, {pct(h0.known_now/h0.estimated_then-1)} more. "
                 f"The bulb kept refilling from inside as recovery improved."},
    ]

    qc_gaps = m.reindex(m.balance_gap_oe.abs().sort_values(ascending=False).index).head(8)
    xb = m[m.cross_border]
    qc = {
        "gaps": [{"field": r.field.title(), "rec": r.recoverable_oe, "cum": r.cum_prod_oe,
                  "rem": r.remaining_oe, "gap": r.balance_gap_oe} for r in qc_gaps.itertuples()],
        "xb": [{"field": r.field.title(), "share": None if pd.isna(r.cross_border_share_pct) else r.cross_border_share_pct,
                "rec": r.recoverable_oe, "gap": r.balance_gap_oe} for r in xb.itertuples()],
    }
    sleip = fi.loc["SLEIPNER"]
    method = [
        f"Width of a field at month <i>m</i> = Sodir's remaining reserves at 31.12.2025 + its reported production after <i>m</i> (minus production in 2026 for later months). Today's widths therefore equal Sodir's remaining reserves ({f0(fi.remaining_oe.sum())} MSm³ o.e., matching the resource accounts) and shut-down fields taper to zero.",
        "Streams start at Sodir's first <i>Producing</i> status date. Test production before that (Troll from 1990, Oseberg 1986, Balder 1991, Grane 1996) is kept in the volumes but does not start the stream. Discovery year is carried for the creaming curve and annotations.",
        f"{int(m.not_yet_producing.sum())} fields approved but not yet producing enter at their PDO approval. Five fields that started in 2026 (Symra, Ørn, Alve Nord, Idun Nord, Eirin) enter in 2026.",
        "Fluids: oil; NGL and condensate merged; gas. Reserves list NGL in million tonnes (× 1.9 to Sm³ o.e.), production lists it in MSm³ already. With that, oil + gas + NGL + condensate reproduces Sodir's o.e. totals to 0.02.",
        f"Sleipner Øst, Sleipner Vest and Gungne are one stream ({f0(sleip.recoverable_oe)} MSm³ o.e.): their production was reported under Sleipner Øst until about 2013, so they balance only as a group.",
        f"Not in the stack: production reported under discoveries with no field (16/1-12 Troldhaugen, 33/9-6 Delta, 7220/11-1 Alta) and Sindre (no 2025 reserves row). All are small.",
        "Cross-border fields carry the Norwegian share only. All ten balance within 0.9 MSm³ o.e., which confirms Sodir's reserves and production use the same share.",
        "Colour: three fluid colours from SubScout's Tide preset. Light mode passes all six palette checks. Dark mode uses a pale NGL &amp; condensate tone to keep colour-blind separation, outside the lightness band: a declared exception.",
    ]
    open_q = [
        "Time direction: top-down (shown) or bottom-up so the bulb grows upward? Decide with the Present-mode layout.",
        "Undiscovered range: the dashed P95/P05 marks use the 2020 resource report (2,200–6,200). Sodir's site blocks automated reads; the 2025 range needs reading in a browser.",
        "Hindsight: add the contemporaneous estimate as a ghost outline on the bulb itself (2004 onward only; earlier field-level estimates are not in FactPages).",
        "Ordering: inside-out by start date (shown). Alternatives: by sea area, or by discovery date so the bulb's core is the oldest finds.",
        "Discovery date as a second state: hatched from discovery to production start would show how long volumes waited.",
        "Maps: quadrant choropleth shown. Alternatives: hex bins, or proportional circles per field with a time slider.",
        "Port the stream graph into SubScout as a generic <code>stream</code> chart type (vertical/horizontal, centred offset, morph between orders).",
    ]

    fields = [{"name": r.field.title(), "area": r.area, "discovery_year": None if pd.isna(r.discovery_year) else int(r.discovery_year),
               "recoverable_oe": r.recoverable_oe, "dominant_fluid": r.dominant_fluid} for r in m.itertuples()]
    for f in streams["fields"]:
        f["name"] = f["key"].title()
        f["area"] = f["area"].replace(" sea", " Sea")
    for f in fields:
        f["area"] = f["area"].replace(" sea", " Sea")

    html = (ROOT / "prototype" / "template.html").read_text()
    repl = {
        "__STREAMS__": json.dumps(streams, ensure_ascii=False, separators=(",", ":")),
        "__HIND__": h.to_json(orient="records"),
        "__POT__": json.dumps(pot),
        "__QUADS__": (D / "quadrants_remaining.geojson").read_text(),
        "__LAND__": (D / "land_simple.geojson").read_text(),
        "__FIELDS__": json.dumps(fields, ensure_ascii=False),
        "__QC__": json.dumps(qc, ensure_ascii=False),
        "__ARC__": json.dumps(arc, ensure_ascii=False),
        "__METHOD__": json.dumps(method, ensure_ascii=False),
        "__OPEN__": json.dumps(open_q, ensure_ascii=False),
        "__PEAK_YEAR__": f"{pk:%Y}",
        "__PEAK__": f0(t.oe.max()),
        "__PEAK_MONTH__": fmt_month(pk),
        "__NOW__": f0(t.oe.iloc[-1]),
        "__NOW_MONTH__": fmt_month(now),
        "__NFIELDS__": str(len(m)),
        "__GASNOW__": pct(t.loc[now, "gas"] / t.loc[now, "oe"]),
        "__GAS1980__": pct(t.loc["1980-12-01", "gas"] / t.loc["1980-12-01", "oe"]),
    }
    for k, v in repl.items():
        html = html.replace(k, v)
    out = ROOT / "prototype" / "index.html"
    out.write_text(html)
    print(f"wrote {out} ({out.stat().st_size/1e6:.2f} MB)")


def fmt_month(d: pd.Timestamp) -> str:
    return f"{d:%B %Y}"


if __name__ == "__main__":
    main()
