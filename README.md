# Tulip

**What the shelf has left: Norway's remaining oil and gas, field by field, 1971 to today.**
Live page: https://admccarthy.github.io/Tulip/

"Tulip" is only the repository's name (the stacked figure's outline suggested it); the page itself is
titled *What the shelf has left*. Every field on the Norwegian continental shelf is drawn as a stream
whose width is the volume it still has to produce: Sodir's latest reserve estimate walked back
through monthly production. The story follows SubScout's `creaming-curve` arc (early giants, long
tail, what's left), with a hindsight section: the same fields held a third more than was estimated
at the time.

A [SubScout](https://github.com/AdmcCarthy/SubScout) story (v0.4.0): `story.md` (narrative, steps,
figure blocks), `story.py` (datasets and every number the prose quotes, each with method, source and
confidence) and `figures/` (custom figure modules: the three-column stream graph on Canvas, circle
packing, creaming curve, rotated maps). Read and Present modes, Sm³ / boe toggle, light and dark.

```
uv sync --all-groups
uv run python scripts/fetch_sodir.py      # -> data/raw (Sodir FactPages + FactMaps; not committed)
uv run python scripts/build_data.py       # -> data/
uv run subscout build . --out _site       # -> the page
uv run python scripts/build_full.py _site # -> _site/full/: full-screen view for screenshots (?theme=dark, ?units=boe)
uv run pytest                             # data checks + every quoted number
```

Pushing to `main` runs the tests, builds with SubScout (warnings fail the build) and deploys to Pages.
Performance is checked with SubScout's `scripts/perf.py` (4x CPU throttle, no frame over 50 ms).

## Data and licence

Data: Sodir (Norwegian Offshore Directorate), Norwegian Licence for Open Government Data (NLOD 2.0);
method in [`data/README.md`](data/README.md) and on the page under "Basis of analysis". Code: MIT License with Acknowledgement.

The quadrant maps are a grid on [Relief](https://github.com/AdmcCarthy/Relief) (Copernicus DEM GLO-90, EMODnet Bathymetry and, east of
43°E, NOAA ETOPO 2022) in its Detuned style at context strength: one column per sea, each Relief's own map view of the North Sea,
the Norwegian Sea or the Barents Sea in its own projection, and one row per snapshot year. `scripts/build_seas.py <Relief dir>` writes
`data/seas.json` (the three views at overview level, with the quadrants and maritime boundaries in the same projection), so the base
and the Sodir quadrants cannot drift apart and no region is joined to another.

## Licence and acknowledgement

MIT License with Acknowledgement ([LICENSE](LICENSE)): the MIT terms plus one condition. Anything built with this work says so,
visibly and in plain words, and does not imply endorsement: "Built with Tulip by Adam McCarthy (https://github.com/AdmcCarthy/Tulip)". The wording is custom, so
the licence is not OSI-approved. Third-party data and vendored code keep their own terms.
