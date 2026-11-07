# Tulip: working rules

**"Tulip" is only the repo name.** The page is titled *What the shelf has left*; never call the figure a
tulip, bulb or flower (or stem, neck, bloom) in reader-facing text. Plain words: shape, total, threads.

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
- Palette (v7): oil green families (forest→leaf | jade→pale mint), gas (brick→orange | amber→pale gold); oil kept
  darker than gas per class for CVD separation. Class names: small, medium, large | giant, giant, super-giant.
- Maps: conic projection rotated (S.map_angle) so the shelf runs up the panel; frame = quadrants with data +
  Norway–Denmark boundary; agreed maritime boundaries drawn dashed.
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
