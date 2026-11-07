# Tulip

**Norway's remaining oil and gas, field by field, 1971 to today.**
Live page: https://admccarthy.github.io/Tulip/

Every field on the Norwegian continental shelf drawn as a stream whose width is the volume it still
has to produce: Sodir's latest reserve estimate walked back through monthly production. Stacked, the
shelf draws a tulip: giants found first, a peak in 2000, a long drawdown with gas at the heart, and
exploration still adding late (Johan Sverdrup). The story follows SubScout's `creaming-curve` arc
(early giants, long tail, what's left), with a hindsight twist: the same fields held a third more
than was estimated at the time.

A [SubScout](https://github.com/AdmcCarthy/SubScout) story (v0.3.0): `story.md` (narrative, steps,
figure blocks), `story.py` (datasets and every number the prose quotes, each with method, source and
confidence) and `figures/` (custom figure modules: the three-column stream graph on Canvas, circle
packing, creaming curve, rotated maps). Read and Present modes, Sm³ / boe toggle, light and dark.

```
uv sync --all-groups
uv run python scripts/fetch_sodir.py      # -> data/raw (Sodir FactPages + FactMaps; not committed)
uv run python scripts/build_data.py       # -> data/
uv run subscout build . --out _site       # -> the page
uv run pytest                             # data checks + every quoted number
```

Pushing to `main` runs the tests, builds with SubScout (warnings fail the build) and deploys to Pages.
Performance is checked with SubScout's `scripts/perf.py` (4x CPU throttle, no frame over 50 ms).

## Data and licence

Data: Sodir (Norwegian Offshore Directorate), Norwegian Licence for Open Government Data (NLOD 2.0);
method in [`data/README.md`](data/README.md) and on the page under "How we know". Code: MIT.
