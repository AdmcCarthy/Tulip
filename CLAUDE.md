# Tulip: working rules

A SubScout story (github.com/AdmcCarthy/SubScout) on NCS remaining reserves over time. Owner: Adam
McCarthy, petroleum geoscience domain expert. Follow SubScout's CLAUDE.md and styleguide.

- Key figure: three linked vertical stream graphs on one scale (liquids, gas, oil equivalent), time running UP
  (1966 to today + 10 years); one stream per field, shade = field size class by total o.e. (same in all three),
  liquids/gas charts oldest-at-centre (younger alternate outward), o.e. chart mixed order (keep the swirl);
  oil = blue, gas = orange, smaller fields deeper shades; Gaussian smoothing + basis curves; thin seams;
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
