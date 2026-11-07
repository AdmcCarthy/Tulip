"""Build Tulip's datasets from the raw Sodir tables in data/raw.

Method (all volumes in million Sm³ oil equivalent, Sodir conventions):
  oil Sm³ = 1 Sm³ o.e.; gas 1000 Sm³ = 1 Sm³ o.e.; NGL: reserves are in million tonnes (x 1.9),
  production is already in MSm³ (x 1); condensate 1:1. NGL and condensate form one group, "liquids".

Remaining reserves of field f, fluid k, at the end of month m are anchored on Sodir's latest estimate
(31.12.2025) and walked back through reported production:

    R_fk(m) = Remaining_fk(2025) + sum of production_fk in the months after m, up to Dec 2025
              (minus production_fk from Jan 2026 to m, for months after the estimate date)

so today's widths equal Sodir's remaining reserves and shut-down fields taper to zero. A field enters
the chart at its production start (Sodir's first 'Producing' status; test production before
that is not a start) (fields approved but not yet producing enter at the PDO
approval month and are flagged). Note this is hindsight: every past width uses today's estimate.

Usage: python scripts/build_data.py [raw_dir] [out_dir]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import Point, shape

import hubs

NGL_T_TO_SM3 = 1.9
FLUIDS = ["oil", "liquids", "gas"]  # liquids = NGL + condensate
ESTIMATE_YEAR = 2025
# Production of Sleipner Vest and Gungne was reported under Sleipner Øst until about 2013 (they share
# processing), so the three only balance as a group. Shown as one stream.
GROUPS = {"SLEIPNER ØST": "SLEIPNER", "SLEIPNER VEST": "SLEIPNER", "GUNGNE": "SLEIPNER"}
# Fields on the UK border; Sodir reports the Norwegian share (verified by the mass balance in tests).
CROSS_BORDER = {
    "STATFJORD": 85.47, "FRIGG": None, "MURCHISON": 22.2, "BLANE": 18, "ENOCH": 20,
    "FLYNDRE": 7, "ISLAY": None, "TOMMELITEN A": 99.57, "UTGARD": 62, "ALVHEIM": None,
}
# Sodir resource accounts as per 31.12.2025 (norskpetroleum.no spreadsheet, MSm³ o.e.).
RESOURCE_ACCOUNTS = {
    "produced": 8969, "reserves": 2165, "contingent_fields": 582,
    "contingent_discoveries": 526, "undiscovered": 3480,
}
# Latest published total range for undiscovered resources found so far: Resource report 2020
# (P95 2,200 / P05 6,200 MSm³ o.e.). PLACEHOLDER until the 2025 range is read from sodir.no.
UNDISCOVERED_RANGE = {"low_p95": 2200, "high_p05": 6200, "as_of": "Resource report 2020"}
UNDISCOVERED_BY_AREA = {"North sea": 545, "Norwegian sea": 760, "Barents sea": 2190}


def d3_orient(geom):
    """Clockwise exteriors (d3's spherical convention); shapely's default is the reverse."""
    from shapely.geometry import MultiPolygon, Polygon
    from shapely.geometry.polygon import orient
    if isinstance(geom, Polygon):
        return orient(geom, sign=-1.0)
    if isinstance(geom, MultiPolygon):
        return MultiPolygon([orient(g, sign=-1.0) for g in geom.geoms])
    return geom


def d(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, format="%d.%m.%Y", errors="coerce")


def load(raw: Path) -> dict[str, pd.DataFrame]:
    names = ["field", "field_reserves", "field_production_monthly", "field_activity_status_hst",
             "discovery"]
    return {n: pd.read_csv(raw / f"{n}.csv") for n in names}


def reserves_by_fluid(res: pd.DataFrame, version: int) -> pd.DataFrame:
    r = res[res.fldVersion == version].copy()
    out = pd.DataFrame({"field": r.fldName.values})
    for kind in ["Recoverable", "Remaining"]:
        out[f"{kind.lower()}_oil"] = r[f"fld{kind}Oil"].values
        out[f"{kind.lower()}_gas"] = r[f"fld{kind}Gas"].values
        out[f"{kind.lower()}_liquids"] = (
            r[f"fld{kind}NGL"].values * NGL_T_TO_SM3 + r[f"fld{kind}Condensate"].values
        )
        out[f"{kind.lower()}_oe"] = r[f"fld{kind}OE"].values
    return out


def production(prod: pd.DataFrame, fields: set[str]) -> tuple[pd.DataFrame, list[str]]:
    p = prod.rename(columns={"prfInformationCarrier": "field"}).copy()
    dropped = sorted(set(p.field) - fields)
    p = p[p.field.isin(fields)]
    p["date"] = pd.to_datetime(dict(year=p.prfYear, month=p.prfMonth, day=1))
    p["oil"] = p.prfPrdOilNetMillSm3
    p["gas"] = p.prfPrdGasNetBillSm3
    p["liquids"] = p.prfPrdNGLNetMillSm3 + p.prfPrdCondensateNetMillSm3
    p["field"] = p.field.replace(GROUPS)
    return p.groupby(["field", "date"], as_index=False)[FLUIDS].sum(), dropped


def walk_back(rem: pd.DataFrame, prod: pd.DataFrame, months: pd.DatetimeIndex,
              entry: pd.Series) -> dict[str, pd.DataFrame]:
    """Remaining at the end of each month, per fluid: wide frames (months x fields)."""
    est = pd.Timestamp(f"{ESTIMATE_YEAR}-12-01")
    out = {}
    for k in FLUIDS:
        w = prod.pivot_table(index="date", columns="field", values=k, aggfunc="sum")
        w = w.reindex(months, fill_value=0).reindex(columns=rem.index, fill_value=0).fillna(0)
        cum = w.cumsum()
        # R(m) = Rem_est + cum(est) - cum(m): adds back production after m (m <= est) and removes
        # production since the estimate (m > est).
        r = rem[f"remaining_{k}"] + (cum.loc[est] - cum)
        mask = np.array([[m >= entry[f] for f in r.columns] for m in r.index])
        out[k] = r.where(mask, 0.0).clip(lower=0)
    return out


def main(raw: Path, out: Path) -> None:
    t = load(raw)
    fld = t["field"].copy()
    rem = reserves_by_fluid(t["field_reserves"], ESTIMATE_YEAR)
    fieldnames = set(rem.field)
    prod, dropped = production(t["field_production_monthly"], fieldnames)

    # group Sleipner
    rem["field"] = rem.field.replace(GROUPS)
    rem = rem.groupby("field").sum(numeric_only=True)

    # metadata
    fld["group"] = fld.fldName.replace(GROUPS)
    disc = t["discovery"].dropna(subset=["fldName"])
    disc_year = disc.assign(g=disc.fldName.replace(GROUPS)).groupby("g").dscDiscoveryYear.min()
    st = t["field_activity_status_hst"].copy()
    st["from"] = d(st.fldStatusFromDate)
    st["group"] = st.fldName.replace(GROUPS)
    pdo = st[st.fldStatus == "Approved for production"].groupby("group")["from"].min()
    producing = st[st.fldStatus == "Producing"].groupby("group")["from"].min()
    shut = st[st.fldStatus == "Shut down"].groupby("group")["from"].max()
    first = prod[prod[FLUIDS].sum(axis=1) > 0].groupby("field").date.min()
    meta = fld.groupby("group").agg(
        area=("fldMainArea", "first"), hc_type=("fldHcType", "first"),
        status=("fldCurrentActivitySatus", lambda s: "Producing" if (s == "Producing").any() else s.iloc[0]),
        npdid=("fldNpdidField", "first"),
    )
    meta = meta.reindex(rem.index)
    meta["discovery_year"] = disc_year.reindex(meta.index)
    meta["pdo"] = pdo.reindex(meta.index)
    # Production start = Sodir's first "Producing" status date (to the month). Earlier test
    # production (e.g. Troll 1990, Balder 1991, Grane 1996) stays in the volumes but does not
    # start the stream.
    meta["first_production"] = producing.reindex(meta.index).dt.to_period("M").dt.to_timestamp()
    meta["first_production"] = meta.first_production.fillna(first.reindex(meta.index))
    meta["first_reported_volume"] = first.reindex(meta.index)
    meta["shut_down"] = shut.reindex(meta.index).where(meta.status == "Shut down")
    meta["not_yet_producing"] = meta.first_production.isna()
    entry = meta.first_production.fillna(meta.pdo)
    meta["entry"] = entry
    meta["cross_border_share_pct"] = [CROSS_BORDER.get(f, np.nan) if f in CROSS_BORDER else np.nan
                                      for f in meta.index]
    meta["cross_border"] = [f in CROSS_BORDER for f in meta.index]
    meta = meta.join(rem)
    hb = hubs.derive(pd.read_csv(raw / "field_description.csv"), sorted(fld.fldName.unique()), GROUPS)
    meta = meta.join(hb.set_index("field")[["hub", "area_name"]])
    meta["hub"] = meta.hub.fillna(pd.Series(meta.index, index=meta.index))

    last = prod.date.max()
    months = pd.date_range("1971-01-01", last, freq="MS")
    R = walk_back(rem, prod, months, entry)

    # QC: width at entry vs recoverable estimate
    start = sum(R[k] for k in FLUIDS).max()
    cum_to_est = prod[prod.date <= f"{ESTIMATE_YEAR}-12-01"].groupby("field")[FLUIDS].sum()
    meta["cum_prod_oe"] = cum_to_est.sum(axis=1).reindex(meta.index).fillna(0)
    meta["balance_gap_oe"] = meta.recoverable_oe - meta.cum_prod_oe - meta.remaining_oe
    meta["peak_width_oe"] = start.reindex(meta.index)
    meta["dominant_fluid"] = meta[[f"recoverable_{k}" for k in FLUIDS]].idxmax(axis=1).str.replace(
        "recoverable_", "")

    # centroids for maps
    geo = json.loads((raw / "fields.geojson").read_text())
    cent = {}
    for ft in geo["features"]:
        if not ft.get("geometry"):
            continue
        nm = ft["properties"]["fldName"]
        cent.setdefault(GROUPS.get(nm, nm), []).append(shape(ft["geometry"]).buffer(0))
    from shapely.ops import unary_union
    cxy = {k: unary_union(v).representative_point() for k, v in cent.items()}
    meta["lon"] = [cxy[f].x if f in cxy else np.nan for f in meta.index]
    meta["lat"] = [cxy[f].y if f in cxy else np.nan for f in meta.index]

    out.mkdir(parents=True, exist_ok=True)
    meta.reset_index(names="field").to_csv(out / "fields.csv", index=False, date_format="%Y-%m-%d")

    # national totals by fluid, monthly
    tot = pd.DataFrame({k: R[k].sum(axis=1) for k in FLUIDS})
    tot["oe"] = tot.sum(axis=1)
    tot.index.name = "date"
    tot.round(3).to_csv(out / "totals_monthly.csv")

    # stream data for the page: quarterly (end of Mar/Jun/Sep/Dec) + last month
    q = months[(months.month % 3 == 0) | (months == months[-1])]
    q = q[q >= "1971-03-01"]
    order = meta.sort_values(["entry"]).index.tolist()
    streams = {
        "dates": [x.strftime("%Y-%m") for x in q],
        "fluids": FLUIDS,
        "fields": [],
    }
    for f in order:
        m = meta.loc[f]
        streams["fields"].append({
            "name": f.title().replace("Øst", "Øst"),
            "key": f,
            "area": m.area,
            "hc": m.hc_type,
            "dominant": m.dominant_fluid,
            "discovered": None if pd.isna(m.discovery_year) else int(m.discovery_year),
            "first_prod": None if pd.isna(m.first_production) else m.first_production.strftime("%Y-%m"),
            "pdo": None if pd.isna(m.pdo) else m.pdo.strftime("%Y-%m"),
            "status": m.status,
            "cross_border": bool(m.cross_border),
            "recoverable": round(float(m.recoverable_oe), 2),
            "remaining": round(float(m.remaining_oe), 2),
            "v": {k: [round(float(x), 2) for x in R[k].loc[q, f].values] for k in FLUIDS},
        })
    (out / "streams.json").write_text(json.dumps(streams, ensure_ascii=False, separators=(",", ":")))

    # hindsight: each year's contemporaneous estimate of remaining reserves vs what we now know was
    # left, for the same set of fields (today's remaining + their production after that year-end)
    hist = []
    res = t["field_reserves"]
    pyear = prod.assign(y=prod.date.dt.year, oe=prod[FLUIDS].sum(axis=1))
    for v in sorted(res.fldVersion.unique()):
        rv = reserves_by_fluid(res, v)
        rv["field"] = rv.field.replace(GROUPS)
        keys = set(rv.field) & set(rem.index)
        later = pyear[(pyear.y > v) & (pyear.y <= ESTIMATE_YEAR) & pyear.field.isin(keys)].oe.sum()
        hist.append({"year": int(v), "n_fields": len(keys),
                     "estimated_then": round(rv[rv.field.isin(keys)].remaining_oe.sum(), 1),
                     "known_now": round(rem.loc[list(keys), "remaining_oe"].sum() + later, 1),
                     "recoverable_then": round(rv[rv.field.isin(keys)].recoverable_oe.sum(), 1),
                     "recoverable_now": round(rem.loc[list(keys), "recoverable_oe"].sum(), 1)})
    pd.DataFrame(hist).to_csv(out / "hindsight.csv", index=False)

    # quadrant snapshots for the maps
    quads = json.loads((raw / "quadrants.geojson").read_text())
    qshapes = [(ft["properties"]["qadName"].strip(), shape(ft["geometry"])) for ft in quads["features"]]
    qof = {}
    for f in meta.index:
        if np.isnan(meta.loc[f, "lon"]):
            continue
        pt = Point(meta.loc[f, "lon"], meta.loc[f, "lat"])
        qof[f] = next((n for n, s in qshapes if s.contains(pt)), None)
    snaps = [1975, 1985, 1995, 2005, 2015, 2025]
    tot_oe = sum(R[k] for k in FLUIDS)
    rows = []
    for y in snaps:
        vals = tot_oe.loc[f"{y}-12-01"]
        for f, v in vals.items():
            if v > 0 and qof.get(f):
                rows.append({"year": y, "quadrant": qof[f], "field": f, "remaining_oe": float(v),
                             "lon": meta.loc[f, "lon"], "lat": meta.loc[f, "lat"]})
    snap = pd.DataFrame(rows)
    snap.to_csv(out / "snapshots_fields.csv", index=False)
    byq = snap.groupby(["year", "quadrant"]).remaining_oe.sum().unstack(0).fillna(0).round(2)
    feats = []
    for n, s in qshapes:
        props = {"q": n}
        if n in byq.index:
            props.update({str(y): float(byq.loc[n, y]) for y in byq.columns})
        feats.append({"type": "Feature", "properties": props,
                      "geometry": json.loads(json.dumps(d3_orient(s.simplify(0.01)).__geo_interface__))})
    (out / "quadrants_remaining.geojson").write_text(json.dumps({"type": "FeatureCollection",
                                                                 "features": feats}))
    (out / "potential.json").write_text(json.dumps({
        "resource_accounts": RESOURCE_ACCOUNTS, "undiscovered_range": UNDISCOVERED_RANGE,
        "undiscovered_by_area": UNDISCOVERED_BY_AREA, "dropped_carriers": dropped,
        "last_month": last.strftime("%Y-%m")}, indent=1))
    # basemap: land clipped to the map frame and simplified for small multiples
    from shapely.geometry import box
    frame = box(-4, 54.0, 30, 75)
    land = unary_union([shape(ft["geometry"]).buffer(0) for ft in
                        json.loads((raw / "land.geojson").read_text())["features"] if ft.get("geometry")])
    land = d3_orient(land.intersection(frame).simplify(0.03))
    sb = json.loads((raw / "sea_boundaries.geojson").read_text())
    lines = [{"type": "Feature", "properties": {"info": ft["properties"].get("informasjon")},
              "geometry": json.loads(json.dumps(shape(ft["geometry"]).intersection(frame).simplify(0.01).__geo_interface__))}
             for ft in sb["features"] if ft.get("geometry")]
    lines = [ln for ln in lines if ln["geometry"]["type"] != "GeometryCollection" or ln["geometry"].get("geometries")]
    (out / "borders.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": lines}))
    (out / "land_simple.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": json.loads(json.dumps(land.__geo_interface__))}]}))
    print(f"{len(meta)} streams, {len(q)} time steps to {last:%Y-%m}; dropped carriers: {dropped}")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(Path(a[0]) if a else Path("data/raw"), Path(a[1]) if len(a) > 1 else Path("data"))
