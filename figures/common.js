// Tulip figure helpers: the fluid palette (linked colour families by field size), theme-aware colour
// lookup, units and a shared tooltip. Uses SubScout's runtime for tokens, units and scheme changes.
import { token, tooltip as ssTooltip, units, UNITS, onSchemeChange, reducedMotion } from "../runtime/js/subscout.js";

// Six size classes per fluid (small -> super-giant). Light: smaller = paler, the smallest almost the white
// of the seams; dark: smaller = closer to the dark background. Oil (with NGL and condensate) in greens,
// gas in dusty clay; muted (chroma <= 0.05 in OKLCH) so the thick giant bodies stay calm.
// Generated in OKLCH: oil (eucalyptus) hue 190, gas (clay) hues 45 -> 34. Muted colours limit colour-blind
// separation of oil vs gas (worst ~3 dE x100); the separate columns and the seams carry that distinction.
const PAL = {
  light: {
    oil: ["#ebf6f5", "#c1ddda", "#a7cbc8", "#92b9b5", "#7ea6a3", "#6c9490"],
    gas: ["#fef4f0", "#f5ddd4", "#eccabe", "#dfb7aa", "#cfa498", "#bf9288"],
    silhouette: "#8798a6",
  },
  dark: {
    oil: ["#202828", "#2f4846", "#41625f", "#587d7a", "#6f9793", "#88b1ae"],
    gas: ["#2e2724", "#59453e", "#7c5e54", "#9b766b", "#b88f83", "#d5a89d"],
    silhouette: "#6e8aa0",
  },
};

export function scheme() {
  const a = document.documentElement.getAttribute("data-colour-scheme");
  if (a === "light" || a === "dark") return a;
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}
export const pal = () => PAL[scheme()];
export const shade = (fluid, cls) => pal()[fluid === "gas" ? "gas" : "oil"][cls];
export const tok = (n) => token(n);
export { onSchemeChange, reducedMotion };

export const unit = () => UNITS[units.get()];
export const fmt0 = d3.format(",.0f");
export const fmt1 = d3.format(",.1f");
/** A volume in MSm³ o.e., shown in the reader's unit (million Sm³ o.e. or million boe). */
export const vol = (msm3, digits = 0) => {
  const u = unit();
  const v = msm3 * u.factor;
  return `${(digits ? fmt1 : fmt0)(v)} million ${u.short}${u.short === "Sm³" ? " o.e." : ""}`;
};
export const volShort = (msm3) => fmt0(msm3 * unit().factor);

let tipInst = null;
export const tip = () => (tipInst ??= ssTooltip());

export const fieldName = (k) => k.split(" ").map((w) => w[0] + w.slice(1).toLowerCase()).join(" ");
export const parseMonth = d3.timeParse("%Y-%m");
export const fmtMonth = d3.timeFormat("%B %Y");

// Shared figure styles on SubScout tokens (injected once).
const CSS = `
.tl-axis,.tl-note{font:400 11px var(--ss-font-body);fill:var(--ss-text-muted)}
.tl-strong{fill:var(--ss-text);font-weight:600}
.tl-col{font:600 12.5px var(--ss-font-body);fill:var(--ss-text)}
.tl-big{font:500 17px var(--ss-font-display);fill:var(--ss-text);paint-order:stroke;stroke:var(--ss-surface);stroke-width:4px}
.tl-label{font:600 11.5px var(--ss-font-body);fill:var(--ss-text);paint-order:stroke;stroke:var(--ss-surface);stroke-width:3px;stroke-linejoin:round;pointer-events:none}
.tl-found{font:italic 400 12.5px var(--ss-font-display);fill:var(--ss-text);paint-order:stroke;stroke:var(--ss-surface);stroke-width:3px}
.tl-sea{font:500 15px var(--ss-font-display);fill:var(--ss-text);paint-order:stroke;stroke:var(--ss-surface);stroke-width:3px}
.tl-area{font:600 11.5px var(--ss-font-body);fill:var(--ss-text);paint-order:stroke;stroke:var(--ss-surface);stroke-width:3px}
.tl-hub{font:500 10.5px var(--ss-font-mono);fill:var(--ss-text-muted);paint-order:stroke;stroke:var(--ss-surface);stroke-width:3px}
.tl-year{font:500 15px var(--ss-font-display);fill:var(--ss-text)}
.tl-legend{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12px;line-height:1.5;margin:0 0 8px;color:var(--ss-text)}
.tl-legend i{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.tl-legend b{font-weight:600;margin-right:2px}
.tl-legend .tl-grp{display:inline-flex;flex-wrap:wrap;gap:4px 10px;align-items:center}
.tl-note-inline{color:var(--ss-text-muted)}
.tl-maps{display:flex;flex-wrap:wrap;gap:10px}
.tl-legend-compact{font-size:11px;gap:2px 10px;margin-bottom:4px}
.tl-legend-compact .tl-grp{gap:2px 8px}
.tl-legend-compact i{width:10px;height:10px;margin-right:3px}
.tl-ev-y{font:500 11.5px var(--ss-font-mono);fill:var(--ss-text);letter-spacing:.04em}
.tl-ev{font:400 12.5px var(--ss-font-body);fill:var(--ss-text-muted)}
`;
if (!document.getElementById("tl-css")) {
  const s = document.createElement("style");
  s.id = "tl-css";
  s.textContent = CSS;
  document.head.append(s);
}

/** Size-class legend: two linked families, oil | gas swatch pairs. */
export function classLegend(legendEl, classes) {
  if (!legendEl) return;
  const P = pal();
  const fam = [["Small to large", classes.filter((c) => c.family === 0)], ["Giant and above", classes.filter((c) => c.family === 1)]];
  if (legendEl.clientWidth && legendEl.clientWidth < 560) {
    legendEl.innerHTML = `<div class="tl-legend tl-legend-compact"><span class="tl-grp"><b>Field size</b>` +
      classes.map((c) => `<span><i style="background:linear-gradient(90deg,${P.oil[c.idx]} 50%,${P.gas[c.idx]} 50%)"></i>${c.short === "Super-giant" ? "Super" : c.short}</span>`).join("") +
      `</span><span class="tl-note-inline">small → large; left half oil, right half gas</span></div>`;
    return;
  }
  legendEl.innerHTML = `<div class="tl-legend">` + fam.map(([t, cs]) => `<span class="tl-grp"><b>${t}</b>` +
    cs.map((c) => `<span><i style="background:linear-gradient(90deg,${P.oil[c.idx]} 50%,${P.gas[c.idx]} 50%)"></i>${c.short} <span class="tl-note-inline">${c.range}</span></span>`).join("") + "</span>").join("") +
    `<span class="tl-note-inline">Million boe recoverable. Eucalyptus green: oil, NGL and condensate; clay: gas. Smaller fields are fainter; the smallest almost vanish into the seams.</span></div>`;
}
