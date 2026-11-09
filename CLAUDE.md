# Tulip: working rules

**"Tulip" is only the repo name.** The page is titled *What the shelf has left*; never call the figure a
tulip, bulb or flower (or stem, neck, bloom) in reader-facing text. Plain words: shape, total, threads.

@../../shared/idiom/CORE.md

Voice and structure of written work (README, docs, published pages) follow Idiom's CORE.md and house style: British English, impersonal, one creative headline then plain varied headings, a section ends on its last point. The import is harmless when the file is absent (CI).

A SubScout story (github.com/AdmcCarthy/SubScout) on NCS remaining reserves over time. Owner: Adam
McCarthy, petroleum geoscience domain expert. Follow SubScout's CLAUDE.md and styleguide.

- Key figure: three linked vertical stream graphs on one scale (liquids, gas, oil equivalent), time running UP
  (1966 to today + 10 years); one stream per field, shade = field size class by total o.e. (same in all three),
  all three charts oldest-at-centre (younger alternate left/right outward);
  size classes: log scale, half-decade steps anchored on giant 500 MMboe and super-giant 5 Bboe:
  <50, 50–160, 160–500 | 500–1,600, 1,600–5,000, ≥5,000 MMboe; two linked colour families per fluid split at giant
  (oil: moss greens -> teal/pale blue; gas: rust/orange -> amber/pale gold), smaller = deeper, wide chroma range,
  checked for CVD (oil vs gas same class ≥ 6.9 ΔE×100); Gaussian smoothing + basis curves; thin seams;
  outlines in the background colour so the many small fields blend and the giants stand out.
- Method: width(m) = Sodir remaining (31.12.2025) + production after m. Streams start at the first
  "Producing" status (production date); discovery year is kept for annotation. Shut-down fields taper to 0.
- Cross-border fields are Norwegian share only (verified by mass balance; see tests).
- Hindsight is part of the story: back-projected widths use today's estimate.
- Numbers in prose are computed (scripts/build_site.py now; story.py later). No typed figures.
- British English; MSm³ o.e. first with boe alongside (1 Sm³ = 6.29 bbl). Observed / Derived / Interpreted.
- Grey silhouette is only a reveal on first view (dissolves into colour).
- Discovery years listed right of the year scale (no in-chart roots).
- Undiscovered resources: left out for now (placeholder). Contingent shown as hatched bar at today.
- Open: port `stream` chart type into SubScout.
- Palette (v8, punchy, after the Sodir original reference figure): oil lime→deep green, gas cream→amber→orange→crimson,
  six size classes, pale = small. Red against green is the weak pair for colour-blind readers and v8 has NOT been
  re-checked for CVD (v7 was); the separate graphs, seams and the lightness order carry the oil/gas distinction.
  Class names: small, medium, large | giant, giant, super-giant.
- Main figure is now two graphs, gas (left) and oil/NGL/condensate (right), with the year axis and the events
  between them (`figures/bulb_pair.js`: bulb.js with `panels`, `gutter`, `autoLabels`); the oil-equivalent total is
  the third figure (`figures/bulb_total.js`, `id: total`). The events text drops out of the gutter below 900px.
- Maps (`figures/seas.js`, data `data/seas.json` from `scripts/build_seas.py <Relief dir>`): a grid, one column per sea (North Sea,
  Norwegian Sea, Barents Sea) and one row per snapshot year. Each column is that Relief region's own map view at its overview level, in
  its own projection (so no rotation, no joining of regions, relief to the frame's edge), with the quadrants that held reserves and the
  agreed maritime boundaries; an arrow in each map shows where north points. A quadrant belongs to the sea Sodir names by latitude
  (62°N and 70°N; tested against Sodir's own sea for all 139 fields). Relief is fetched with its `scripts/fetch_data.py`; its data are
  never committed here. The earlier conic map over a joined five-region base (and its GEBCO fill) was replaced by this.
- Circle packing: sea → hub → field (hub parsed from Sodir development text, scripts/hubs.py); snapshots
  recoverable / left 1995 / 2005 / today; zoomable.
- Now a SubScout story (v0.3.0 custom figures): story.md + story.py + figures/*.js; build with
  `uv run subscout build . --out _site`; CI fails on build warnings. Every number in prose comes from
  story.py and has a test in tests/test_story.py (years typed in prose are asserted there too).
- figures/bulb.js renders on Canvas with one pre-painted canvas per scroll state (opts.states) so steps
  only cross-fade; keep it that way or the perf gate (SubScout scripts/perf.py, 4x throttle) fails.
- Declared exceptions live in the chart blocks (direct-labels, north-up); the truth gate still applies.
- The first scrolly uses SubScout's `layout=wide` (v0.3.1): full-width figure frame, cards in a lane.
  The bulb's height is 5% below v0.2 and capped so its title and legend fit on screen.
- Full-screen view: scripts/build_full.py writes _site/full/ (bulb.js poster mode: events from story.py
  in the left margin, discovery years right of the year scale, labels dodge each other; dashed discovery-to-
  first-oil lines for Troll and Johan Sverdrup; Light/Dark toggle). For screenshots.

- Figure widths: the total (`bulb_total.js`) takes 60% of the frame (`TOTAL_FRAC` in bulb.js), with a width bar and a note of its scale
  against the pair; nothing is labelled on its side (names go horizontal, only where the stream is wide enough).
- Without the giants (fields under 500 MMboe, size classes 0 to 2; the first paragraph and the additions chart use all three):
  the figure shows small and medium (classes 0 and 1, under 160 MMboe) as three graphs side by side, combined, small, medium,
  on one stretched scale (`figures/bulb_trio_stretched.js`, with a bar and a note of the stretch against the total). A version on the
  total's own scale was dropped: the graphs were slivers too thin to read. Large fields (160 to 500) are left out of the figure and
  named as such in the prose. bulb.js options
  `groups` (one graph per group of size classes, equal slots), `classes`, `lift` (steps shades up the ramp), `scaleWith`,
  `scaleNote` ("pair" or "total"), `scaleBar`.
  A field is "added" in the quarter it enters its stream at its remaining volume then; fields approved and not yet
  producing enter at approval (these drive the 2023 jump); "produced" = added minus the change in what is left
  (story.py `_small`, `_flows`; tests recompute from the raw files). Hindsight: older fields carry more reserve growth.

## Idiom (private repo)

Idiom is Adam McCarthy's private repo (`github.com/AdmcCarthy/Idiom`; `gh repo clone AdmcCarthy/Idiom` with access, normally linked at
`../../shared/idiom`) of voice, house style, working rules and the lookup tables agents use first: `DIRECTORY.md` says which repo already
does a job, `DATASETS.md` gives every dataset's terms, attribution line and status. Read the relevant one before choosing a repo or
using data, and update it when you learn something new. Never copy anything from its `personal/` or `working/` folders into this repo
or quote it in public output; if the folder is not available, say so and carry on with this file.
