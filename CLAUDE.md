# Tulip: working rules

A SubScout story (github.com/AdmcCarthy/SubScout) on NCS remaining reserves over time. Owner: Adam
McCarthy, petroleum geoscience domain expert. Follow SubScout's CLAUDE.md and styleguide.

- Key figure: vertical stream graph, one stream per field split by fluid (oil; NGL + condensate; gas),
  outlines in the background colour so the many small fields blend and the giants stand out.
- Method: width(m) = Sodir remaining (31.12.2025) + production after m. Streams start at the first
  "Producing" status (production date); discovery year is kept for annotation. Shut-down fields taper to 0.
- Cross-border fields are Norwegian share only (verified by mass balance; see tests).
- Hindsight is part of the story: back-projected widths use today's estimate.
- Numbers in prose are computed (scripts/build_prototype.py now; story.py later). No typed figures.
- British English; MSm³ o.e. first with boe alongside (1 Sm³ = 6.29 bbl). Observed / Derived / Interpreted.
- Open: time direction, undiscovered range (2025 values), port `stream` chart type into SubScout.
