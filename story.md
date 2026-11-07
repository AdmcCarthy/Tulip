---
title: What the shelf has left
short_title: "What the shelf has left"
dek: Norway found its biggest oil and gas fields first. The volume its continental shelf still had to produce grew for three decades, peaked as the century turned and has fallen ever since, held up by a few giants and the many smaller fields around them.
kicker: NCS · Remaining reserves 1971–2026 · Sodir
byline: Adam McCarthy
date: 2026-11-07
arc: creaming-curve
register: section
palette: tide
surface: nordic-cool
units: sm3
horizon: true
kpis:
  - { metric: peak_total, filter: volume, label: "left to produce at the peak, in 2000" }
  - { metric: now_total, filter: volume, label: "left to produce today" }
  - { metric: gas_share_now, filter: pct, label: of what is left is gas }
  - { metric: n_fields, label: fields in the stack }
sources:
  sodir:
    name: Sodir FactPages and FactMaps
    url: https://factpages.sodir.no
    accessed: 2026-11-07
    note: Field reserves (versions 2004–2025), monthly production, field status, descriptions, discoveries; fields, quadrants, land and maritime boundaries. NLOD 2.0.
  ra:
    name: Sodir resource accounts, 31.12.2025
    url: https://www.norskpetroleum.no/en/petroleum-resources/resource-accounts/
    accessed: 2026-11-07
    note: Totals by resource class (norskpetroleum.no spreadsheet)
data:
  streams: data/streams.json
  fields: data/fields.csv
  totals: data/totals_monthly.csv
  hindsight: data/hindsight.csv
  potential: data/potential.json
  snap: data/snapshots_fields.csv
  quads: data/quadrants_remaining.geojson
  land: data/land_simple.geojson
  borders: data/borders.geojson
---

Every oil and gas field has a volume it can still produce. Sodir, the Norwegian Offshore
Directorate, publishes today's estimate for each field and every month of production since 1971.
Add the production back, month by month, and you can draw what each field had left at any point in
its life. Stack all {{ n_fields }} fields and the whole shelf takes one shape: a narrow base in the
1970s, a broad middle around 2000 and a narrowing top today.

Read the figure upwards. Time runs from the first oil at the bottom to today, with ten years of open
space above.

::: step {beat=early-giants kicker="The whole shelf" layout=wide}
### Oil, gas and the two together

Each thread is one field: oil, NGL and condensate in green, gas in orange, the two added together
on the right. At its widest, early in 2000, the shelf had {{ peak_total | volume }} left to produce.
Today {{ now_total | volume }} remain, {{ fall_since_peak | pct }} less. The oldest fields sit at
the centre of each column and younger ones outward; deep shades are small fields and pale shades
giants.

```chart
id: bulb
type: custom
module: figures/bulb.js
data: bulb
register: outcrop
state: { mode: colour }
title: Remaining reserves peaked in 2000 and have fallen by {{ fall_since_peak | pct }} since
subtitle: Remaining recoverable volume per field, million Sm³ o.e., time running up
source: sodir
confidence: derived
unit: million Sm³ o.e.; 1 Sm³ o.e. = 6.29 boe
notes: Width = Sodir's estimate at 31.12.2025 plus production since each month (hindsight). Streams start at each field's production start and are smoothed over about a year for display; hover values are not smoothed.
exception: { rule: direct-labels, reason: "Around 1,200 streams: shade encodes six size classes in two linked colour families per fluid, with a legend, hover and selective labels instead of direct labels. Width has no axis; the columns share one scale and the hover gives values." }
```
:::

::: step {beat=early-giants kicker="1969–1979"}
### The first field: Ekofisk

Ekofisk was found in 1969 and came on stream in June 1971. Until Frigg, Cod and Vest Ekofisk joined
in 1977 it was the whole shelf: {{ ekofisk_rec | volume }} recoverable by today's estimate, and still among the largest fields
on the shelf.

```chart
use: bulb
mode: colour
focus: [EKOFISK]
```
:::

::: step {beat=early-giants kicker="1979–1992"}
### The giants arrive

Statfjord came on stream in 1979, Gullfaks and Oseberg in the late 1980s, Snorre in 1992. The
{{ n_giants }} giants, fields of more than {{ 500 | param }} million barrels of oil equivalent, hold
{{ giant_share | pct }} of everything ever booked on the shelf. The ten largest alone hold
{{ top10_share | pct }}.

```chart
use: bulb
mode: colour
classes: [3, 4, 5]
focus: [STATFJORD, GULLFAKS, OSEBERG, SNORRE]
```
:::

::: step {beat=early-giants kicker="1995"}
### Gas at the heart

Troll was found in 1979 and began production in 1995. It added {{ troll_jump | volume }} to the
shelf's total in a single month: {{ troll_rec | volume }} recoverable, the only super-giant on the shelf. In
1980 gas was {{ gas_share_1980 | pct }} of what was left. It has outweighed oil, NGL and condensate
together since the end of 2003, and today {{ gas_share_now | pct }} of the remainder is gas.

```chart
use: bulb
mode: colour
focus: [TROLL]
```
:::

::: step {beat=long-tail kicker="The long tail"}
### Many small fields

{{ n_sub_giant }} of the {{ n_fields }} fields are below giant size. Between them they hold
{{ sub_giant_share | pct }} of the volume: the deep-coloured threads at the edges of each column.
Most are produced through an existing platform rather than one of their own.

```chart
use: bulb
mode: colour
classes: [0, 1, 2]
```
:::

::: step {beat=long-tail kicker="2019"}
### A late giant

Johan Sverdrup was found in 2010 on the Utsira High, in a part of the North Sea that had been
explored for four decades. When it started in October 2019 it added {{ sverdrup_jump | volume }} at
once: the last big step outward in the shape.

```chart
use: bulb
mode: colour
focus: [JOHAN SVERDRUP]
```
:::

See all three columns full screen, with the main events marked, in the [full-screen view](full/).

## Less was known at the time

Every width in the figure uses today's estimate. That is hindsight. At the end of 2004, Sodir's field
tables put {{ then_2004 | volume }} left in the {{ n_fields_2004 }} fields then booked. We now know
those same fields held {{ known_2004 | volume }}, {{ growth_2004 | pct }} more. The difference is
reserve growth: better recovery, more wells and longer field lives. Existing fields kept adding
reserves from the inside.

```chart
id: hindsight
type: line
data: hind
x: year
y: value
series: series
volume: true
focus: [Known now]
unit_label: "million {unit}"
title: The same fields held {{ growth_2004 | pct }} more than Sodir estimated in 2004
subtitle: Remaining reserves at each year end, million Sm³ o.e., for the fields in that year's table
source: sodir
confidence: derived
unit: million Sm³ o.e.
notes: "Estimated at the time: Sodir's field reserve table for that year. Known now: today's remaining plus production since, for the same fields. Field-level estimates before 2004 are not published in FactPages."
```

## The biggest came first

Plot each field's size against the year it was found and the classic creaming curve appears. The
giants cluster before 1990; most later discoveries are small. Johan Sverdrup is the exception that
keeps exploration in a mature basin worthwhile.

```chart
id: creaming
type: custom
module: figures/cream.js
data: bulb
title: Most giants were found before 1990; later finds are mostly small
subtitle: Recoverable volume against discovery year, million Sm³ o.e., log scale
source: sodir
confidence: observed
notes: Fields only. Discoveries not yet developed are not shown, which flatters the recent decades less than it might.
exception: { rule: direct-labels, reason: "139 points: colour shows fluid and size class (legend), the largest fields are labelled and hover gives the rest." }
```

## The centre of gravity moves north

In 1995 almost all of what was left lay in the North Sea. Today {{ north_share_now | pct }} lies in
the Norwegian and Barents Seas, up from {{ north_share_1995 | pct }} at the end of 1995.

```chart
id: maps
type: custom
module: figures/maps.js
data: [quads, land, borders]
title: Remaining reserves spread north as the North Sea giants drained
subtitle: Remaining recoverable volume by Sodir quadrant at the end of each snapshot year
source: sodir
confidence: derived
notes: Fields assigned to the quadrant holding a point inside their outline. Dashed lines are agreed maritime boundaries.
exception: { rule: north-up, reason: "Maps rotated so the shelf runs up each panel and the frame leaves out empty land to the east; a north arrow marks the turn." }
```

## How the shelf is wired

::: step {beat=long-tail kicker="Sea, area, hub, field"}
### Hubs and the fields that feed them

Group each field under the platform that produces it, and each platform under its area.
{{ n_tied }} of the {{ n_fields }} fields are produced through another field's facilities, hosted
by {{ n_hubs }} hubs. Click a circle to zoom in.

```chart
id: pack
type: custom
module: figures/pack.js
data: bulb
state: { t: rec }
title: A few large hubs carry clusters of small tie-backs
subtitle: Sea, area, hub and field; circle area = recoverable volume, million Sm³ o.e.
source: sodir
confidence: interpreted
notes: Hubs read from Sodir's development descriptions (tied back, connected or processed at a named field's facility), chains resolved to the final host. Areas are the nearest named area in each sea, with a few overrides; see How we know.
exception: { rule: direct-labels, reason: "Circle packing with four levels: larger circles are labelled, hover and zoom give the rest." }
```
:::

::: step {beat=long-tail kicker="1995"}
### 1995: the giants still full

Each circle now shows what that field had left at the end of 1995. The North Sea giants dominate;
the Norwegian Sea is still filling.

```chart
use: pack
t: "1995-12"
```
:::

::: step {beat=long-tail kicker="2005"}
### 2005: drawing down

Ten years on, Statfjord, Gullfaks and Oseberg have shrunk, and Haltenbanken in the Norwegian Sea
carries more of the weight. The Barents Sea has no producing field yet; Snøhvit starts in 2007.

```chart
use: pack
t: "2005-12"
```
:::

::: step {beat=whats-left kicker="Today"}
### What is left

Today the remainder is concentrated: Troll and Johan Sverdrup hold {{ big2_share | pct }} of it.
Around them, hubs keep producing through ever smaller tie-backs.

```chart
use: pack
t: now
```
:::

## What keeps the shelf producing

The top of the shape is narrowing. Production in the past twelve months would use up today's remaining reserves
in about {{ rp_years | round:0 }} years if nothing were added. That is a ratio, not a forecast:
production declines as fields age, and reserves grow as they did after 2004. Another
{{ contingent | volume }} has been found but not yet sanctioned.

What the figure shows is how Norway has kept the shelf producing so far: a handful of giants found early,
reserve growth inside them, and a long tail of smaller fields tied back to the platforms the giants
built. Whether the next ten years add another step outward depends on exploration and on sanctioning
what has already been found. *Interpreted.*

::: appendix
### Method

- **Width of a field in a month** = Sodir's remaining reserves at the end of 2025 plus the field's
  reported production after that month (minus production since, for 2026). Today's widths therefore
  equal Sodir's remaining reserves, and fields that have shut down taper to zero.
- **Start of a stream** = Sodir's first *Producing* status date. Test production before that (Troll
  from 1990, Oseberg 1986, Balder 1991, Grane 1996) is kept in the volumes but does not start the
  stream.
- **Fluids**: oil, NGL and condensate are shown together as liquids. Reserves list NGL in million
  tonnes (× {{ 1.9 | param }} to Sm³ o.e.); production lists it in Sm³. Gas: a thousand Sm³ count as one Sm³ o.e.
- **Groups**: Sleipner Øst, Sleipner Vest and Gungne are one stream, because their production was
  reported under Sleipner Øst until about 2013.
- **Cross-border fields** (Statfjord, Frigg, Murchison, Blane, Enoch, Flyndre, Islay, Tommeliten A,
  Utgard, Alvheim) carry the Norwegian share only; all balance within {{ xb_max_gap | volume:1 }}.
- **Size classes**: total recoverable volume on a log scale in half-decade steps anchored on giant
  ({{ 500 | param }} million boe) and super-giant ({{ 5 | param }} billion boe): small, medium, large, two giant steps, and
  super-giant. Two linked colour families per fluid split at giant size; oil is kept darker than gas
  in each class so the two stay apart for colour-blind readers.
- **Hubs and areas** are an interpretation: hubs read from Sodir's development descriptions; areas
  from the nearest named area in each sea, with overrides for Valhall (southern North Sea), Grane
  (Frigg–Alvheim–Balder), Martin Linge (Oseberg–Troll) and Yggdrasil (Hugin, Munin and Fulla).
- **Not included**: undiscovered resources, and production reported under three discoveries that are
  not fields (Troldhaugen, Delta and Alta) or under Sindre.

### Glossary

- **Sm³ o.e.**: standard cubic metres of oil equivalent; one Sm³ o.e. is {{ 6.29 | param }} barrels of oil equivalent (boe).
- **Reserves**: volumes in sanctioned developments still to be produced. **Contingent resources**:
  found but not yet sanctioned.
- **PDO**: plan for development and operation, the sanction step on the Norwegian shelf.
- **Tie-back**: a field produced through another field's platform or vessel.
- **Creaming curve**: field size against discovery order; the largest fields tend to be found first.
:::
