"""Derive each field's production hub (host facility) and named area from Sodir's field descriptions.

Hub: the field whose facility a field is tied back to, connected to, or processed on, found in the
'Development' text (e.g. "tied to the Åsgard B facility" -> ÅSGARD). A field with no host is its own hub.
Area: a named area in the text ("in the Tampen area", "on the Utsira High", "Haltenbanken").
"""

from __future__ import annotations

import re

import pandas as pd

VERBS = r"(?:tied(?:-|\s)?(?:back|in)?|connected|processed|hooked up)"
HOST = re.compile(VERBS + r"\s+(?:\w+\s+){0,3}?(?:to|at|on|via)\s+(?:the\s+)?([A-ZÆØÅ][\w\-ÆØÅæøå]*(?:\s+[A-ZÆØÅ0-9][\w\-ÆØÅæøå]*){0,2})")
AREA = re.compile(r"(?:in|on) the ((?:[A-ZÆØÅ][\wæøå\-]+\s){1,2}(?:area|High|Basin|Platform|Terrace)|Haltenbanken|Tampen area)")


def match_field(token: str, names: list[str], self_name: str) -> str | None:
    t = token.upper()
    best = None
    for n in names:
        if n == self_name:
            continue
        if t == n or t.startswith(n + " "):
            if best is None or len(n) > len(best):
                best = n
    return best


def derive(desc: pd.DataFrame, names: list[str], groups: dict[str, str]) -> pd.DataFrame:
    rows = []
    dev = desc[desc.fldDescriptionHeading == "Development"].set_index("fldName").fldDescriptionText
    allt = desc.groupby("fldName").fldDescriptionText.apply(" ".join)
    for n in names:
        text = dev.get(n, "") or ""
        host = None
        for m in HOST.finditer(text):
            host = match_field(m.group(1), names, n)
            if host:
                break
        a = AREA.search(allt.get(n, "") or "")
        rows.append({"field": n, "host": host, "area_name": a.group(1).replace(" area", "") if a else None})
    out = pd.DataFrame(rows)
    out["field"] = out.field.replace(groups)
    out["host"] = out.host.replace(groups)
    out = out.groupby("field").first().reset_index()
    # resolve chains (A tied to B tied to C -> C) and self-hosting after grouping
    h = dict(zip(out.field, out.host))
    def root(f, seen=()):
        x = h.get(f)
        if x is None or pd.isna(x) or x == f or x in seen:
            return f
        return root(x, seen + (f,))
    out["hub"] = [root(f) for f in out.field]
    return out


# ------------------------------------------------------------------------- areas
# A middle level between sea and hub: named petroleum areas. Each hub (or stand-alone field) goes to the
# nearest anchor in its sea, with overrides where geography alone misleads. Anchors are approximate
# (lon, lat) centres; names follow common Sodir and industry usage.
AREA_ANCHORS = {
    "North sea": {
        "Greater Ekofisk": (3.2, 56.5),
        "Southern North Sea": (2.85, 57.1),
        "Sleipner": (1.9, 58.4),
        "Utsira High": (2.4, 58.85),
        "Frigg–Alvheim–Balder": (2.2, 59.5),
        "Oseberg–Troll": (3.3, 60.7),
        "Tampen": (2.1, 61.3),
    },
    "Norwegian sea": {
        "Haltenbanken": (7.0, 64.9),
        "Nordland (Norne–Skarv)": (7.9, 65.9),
        "Møre (Ormen Lange)": (5.5, 63.4),
        "Vøring (Aasta Hansteen)": (6.9, 67.1),
    },
    "Barents sea": {
        "Hammerfest Basin": (21.6, 71.4),
        "Bjørnøyrenna (Johan Castberg)": (20.3, 72.5),
    },
}
AREA_OVERRIDES = {  # by hub
    "VALHALL": "Southern North Sea",  # closer to Ekofisk on the map, but its own cluster with Hod and Fenris
    "MARTIN LINGE": "Oseberg–Troll",
    "HUGIN": "Yggdrasil",
    "GRANE": "Frigg–Alvheim–Balder",
}
HUB_OVERRIDES = {"EMBLA": "ELDFISK"}  # Embla is remotely operated from and produces to Eldfisk
HUB_NAMES = {"HUGIN": "Yggdrasil"}  # the Hugin, Munin and Fulla development is known as Yggdrasil


def areas(meta: pd.DataFrame) -> pd.Series:
    """meta: index = field, columns area (sea), hub, lon, lat. Returns the area name per field."""
    out = {}
    for f, r in meta.iterrows():
        hub = r.hub
        if hub in AREA_OVERRIDES:
            out[f] = AREA_OVERRIDES[hub]
            continue
        h = meta.loc[hub] if hub in meta.index else r
        lon, lat = (h.lon, h.lat) if pd.notna(h.lon) else (r.lon, r.lat)
        anchors = AREA_ANCHORS.get(r.area, {})
        if not anchors or pd.isna(lon):
            out[f] = None
            continue
        k = 1 / 0.5  # 1 degree of longitude is about half a degree of latitude here
        out[f] = min(anchors, key=lambda a: ((anchors[a][0] - lon) / k) ** 2 + (anchors[a][1] - lat) ** 2)
    return pd.Series(out)
