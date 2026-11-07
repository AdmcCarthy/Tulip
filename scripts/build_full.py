"""Write the full-screen view of the three-column figure to <site>/full/index.html.

Run after `subscout build . --out _site` (it reuses the site's runtime CSS/JS and figures/). Data and
numbers come from story.py through SubScout's own loader, so the view always matches the story.
Options in the URL for screenshots: ?theme=light|dark, ?units=sm3|boe.

Usage: python scripts/build_full.py [site_dir]
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import yaml
from subscout.build import Report, load_data, load_story_module

ROOT = Path(__file__).resolve().parents[1]


def main(site: Path) -> None:
    fm = yaml.safe_load((ROOT / "story.md").read_text(encoding="utf-8").split("---")[1])
    rep = Report()
    d = load_data(ROOT, fm["data"], rep)
    mod = load_story_module(ROOT)
    bulb = mod.datasets(d)["bulb"]
    m = mod.metrics(d)
    if rep.errors:
        raise SystemExit("\n".join(rep.errors))
    fall = round(m["fall_since_peak"].value * 100)
    src = fm["sources"]["sodir"]
    title = f"Norway's remaining oil and gas peaked in 2000 and has fallen by {fall}% since"
    page = f"""<!doctype html>
<html lang="en-GB" data-type="ledger" data-palette="{fm.get('palette', 'tide')}" data-surface="{fm.get('surface', 'nordic-cool')}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(fm['title'])} · full view</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="../runtime/css/tokens.css">
<link rel="stylesheet" href="../runtime/css/base.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<style>
  html, body {{ height: 100%; margin: 0; }}
  body {{ background: var(--ss-surface); color: var(--ss-text); font-family: var(--ss-font-body);
         display: grid; grid-template-rows: auto 1fr auto; min-height: 100vh; }}
  header, footer {{ padding: 20px 32px 0; }}
  .kicker {{ font: 500 12px/1.4 var(--ss-font-mono); letter-spacing: .08em; text-transform: uppercase; color: var(--ss-text-muted); }}
  h1 {{ font: 500 clamp(1.6rem, 2.4vw, 2.3rem)/1.15 var(--ss-font-display); margin: 6px 0 4px; letter-spacing: -0.01em; }}
  .sub {{ margin: 0 0 10px; color: var(--ss-text-muted); font-size: 14px; }}
  main {{ min-height: 0; padding: 0 32px; }}
  #fig {{ height: 100%; }}
  footer {{ padding: 8px 32px 16px; font-size: 12px; color: var(--ss-text-muted); display: flex; flex-wrap: wrap; gap: 4px 20px; }}
  footer b {{ font: 500 11px var(--ss-font-mono); letter-spacing: .06em; text-transform: uppercase; margin-right: 6px; color: var(--ss-text); }}
  .tl-col {{ font-size: 14px !important; }}
  .tools {{ position: fixed; top: 14px; right: 24px; display: flex; gap: 14px; align-items: center; z-index: 5; }}
  .back {{ font-size: 12px; color: var(--ss-link); }}
  @media print {{ .tools {{ display: none; }} }}
</style>
</head>
<body>
<div class="tools">
  <div class="ss-seg" id="ctl-theme" role="group" aria-label="Colour scheme"><button data-value="light">Light</button><button data-value="dark">Dark</button></div>
  <a class="back" href="../">Back to the story</a>
</div>
<header>
  <div class="kicker">{html.escape(fm.get('kicker', ''))}</div>
  <h1>{html.escape(title)}</h1>
  <p class="sub">Remaining recoverable oil and gas in every field on the Norwegian continental shelf, month by month, by today's estimate. Each thread is one field; time runs up the page.</p>
  <div id="legend"></div>
</header>
<main><div id="fig"></div></main>
<footer>
  <span><b>Source</b>{html.escape(src['name'])}, accessed {src['accessed']}; analysis admccarthy.github.io/Tulip</span>
  <span><b>Method</b>Sodir's 31.12.2025 estimate plus production since each month (hindsight); smoothed over about a year</span>
  <span><b>Units</b><span id="unit-note">million Sm³ o.e.; 1 Sm³ o.e. = 6.29 boe</span></span>
  <span><b>Confidence</b>Derived</span>
</footer>
<script type="application/json" id="data">{json.dumps({"bulb": bulb}, ensure_ascii=False).replace("</", "<\\/")}</script>
<script type="module">
  import {{ theme, units, onSchemeChange, bindSeg }} from "../runtime/js/subscout.js";
  import create from "../figures/bulb.js";
  const q = new URLSearchParams(location.search);
  if (q.get("theme")) theme.set(q.get("theme"));
  // Light/Dark only: resolve "system" to what the reader sees now, so one of the two is always pressed
  if (theme.get() === "system") theme.set(matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  bindSeg(document.getElementById("ctl-theme"), theme);
  if (q.get("units")) units.set(q.get("units"));
  if (units.get() === "boe") document.getElementById("unit-note").textContent = "million boe (1 Sm³ o.e. = 6.29 boe)";
  const data = JSON.parse(document.getElementById("data").textContent);
  const el = document.getElementById("fig");
  const chart = create(el, data, {{ legendEl: document.getElementById("legend"), states: [{{ mode: "colour" }}], poster: {{ height: () => el.parentElement.clientHeight, roots: ["TROLL", "JOHAN SVERDRUP"] }} }});
  const draw = () => chart.draw(el.clientWidth, {{ mode: "colour" }});
  draw();
  let w = 0;
  let h = 0;
  new ResizeObserver(() => {{ const p = el.parentElement; if (el.clientWidth !== w || p.clientHeight !== h) {{ w = el.clientWidth; h = p.clientHeight; draw(); }} }}).observe(el.parentElement);
  onSchemeChange(() => chart.repaint());
</script>
</body>
</html>
"""
    out = site / "full"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    print(f"wrote {out / 'index.html'}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site")
