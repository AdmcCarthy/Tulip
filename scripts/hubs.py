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
