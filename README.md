# Tulip

**Norway's remaining oil and gas, field by field, 1971 to today.**
Live page: https://admccarthy.github.io/Tulip/

Every field on the Norwegian continental shelf drawn as one stream whose width is the volume it has
left to produce: Sodir's latest reserve estimate walked back through monthly production. Stacked, the
shelf draws a tulip bulb: the giants found first, a peak in 2000, a long drawdown with gas at the
heart, and exploration still adding late (Johan Sverdrup). Supporting figures: what was estimated at
the time against what we now know (hindsight), the creaming curve, remaining volume by quadrant, and
a circle packing of sea, area, hub and field.

Built in the style of [SubScout](https://github.com/AdmcCarthy/SubScout) (tokens, type, confidence
levels, sources). The figures are custom and declare their own exceptions; see `CLAUDE.md`.

```
uv sync --all-groups
uv run python scripts/fetch_sodir.py      # -> data/raw (Sodir FactPages + FactMaps; not committed)
uv run python scripts/build_data.py       # -> data/
uv run python scripts/build_site.py       # -> _site/index.html (+ prototype/index.html fragment)
uv run pytest
```

Pushing to `main` runs the tests, builds the page from the committed `data/` and deploys to GitHub Pages.

## Data and licence

Data: Sodir (Norwegian Offshore Directorate), Norwegian Licence for Open Government Data (NLOD 2.0);
details and method in [`data/README.md`](data/README.md). Code: MIT (see `LICENSE`).
