"""The header band for the story's hero: a synthetic section with a geometry the eye reads, in
SubScout's header contract (docs/header-contract.md in SubScout). No horizons, no surfaces.

Needs seismic_art (its interpreter):

    uv run --project ..\\seismic_art python scripts\\make_header.py

A convolutional model from seismic_art.header.synthetic_hero: folded layers thinning onto an
anticline, one normal fault, an angular unconformity with flat layers above. Not Sodir data and not a
real survey; the page says so. Writes data/header.json (about 85 kB).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from seismic_art import export_json
from seismic_art.header import synthetic_hero

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "header.json")
    a = ap.parse_args()
    payload = synthetic_hero(
        seed=a.seed,
        label="synthetic section: folded layers under an unconformity, one fault; no real survey",
    )
    payload["title"] = "Tulip: the header band"
    path = export_json(a.out, payload)
    print(f"wrote {path} ({path.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
