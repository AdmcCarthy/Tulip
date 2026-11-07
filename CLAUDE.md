# Tulip: working rules

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
- Numbers in prose are computed (scripts/build_prototype.py now; story.py later). No typed figures.
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
