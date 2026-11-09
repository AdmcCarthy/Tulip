# Data

All data from **Sodir** (Norwegian Offshore Directorate), Norwegian Licence for Open Government Data
(NLOD 2.0), credited as "Source: Sodir". `data/raw/` is fetched by `scripts/fetch_sodir.py` and not
committed; everything else here is built by `scripts/build_data.py`. Don't hand-edit.

| File | What | Confidence |
|---|---|---|
| `fields.csv` | One row per stream (field or field group): area, fluids, discovery year, PDO, production start, recoverable/remaining by fluid, QC gap, centroid | Observed / Derived |
| `streams.json` | Quarterly remaining reserves per field per fluid (oil; NGL+condensate; gas), MSm³ o.e. | Derived |
| `totals_monthly.csv` | NCS total remaining by fluid, monthly | Derived |
| `hindsight.csv` | Each year's Sodir estimate of remaining (versions 2004–2025) vs today's back-projection, same fields | Derived |
| `quadrants_remaining.geojson`, `snapshots_fields.csv` | Remaining by quadrant at 1975…2025 | Derived |
| `potential.json` | Sodir resource accounts 31.12.2025 (norskpetroleum.no spreadsheet) + undiscovered range | Observed / Interpreted |
| `land_simple.geojson` | Sodir FactMaps basemap land, clipped and simplified (kept as a build input; the maps draw Relief's own land) | Observed |
| `seas.json` | The three Relief map views (North Sea, Norwegian Sea, Barents Sea) at overview level, in each region's own projection (units of 100 m), with the quadrants that held reserves and the maritime boundaries; built by `scripts/build_seas.py` | Derived |

Raw sources (accessed 2026-11-07): FactPages tables `field`, `field_reserves`, `field_in_place_volumes`,
`field_production_monthly`, `field_activity_status_hst`, `field_description`, `field_operator_hst`,
`discovery`, `discovery_reserves`; FactMaps layers 7100 (fields), 1002 (quadrants), basemap 5 (land).
Resource accounts: norskpetroleum.no/wp-content/uploads/74-Ressursregnskap-totalt-tabell-20022026.xlsx.

Known quirks: NGL in reserves is million tonnes (× 1.9), in production MSm³. Sleipner Øst/Vest/Gungne
balance only as a group. Test production precedes the production-start status for Troll, Oseberg,
Balder, Grane, Mime, Gimle. Undiscovered P95/P05 range is a placeholder from the 2020 resource report.

Hubs and areas (`fields.csv` columns `hub`, `area_group`): hub = host facility parsed from Sodir's
'Development' descriptions (`scripts/hubs.py`; tied/connected/processed to a named field's facility,
chains resolved). Areas: nearest named anchor per sea with documented overrides. Interpreted grouping;
checked by `tests/test_hubs.py`.

`header.json` is the band in the page's hero: a synthetic seismic section made by `scripts/make_header.py` (seismic_art's `synthetic_hero`), not Sodir data and not a real survey; the page says so.
