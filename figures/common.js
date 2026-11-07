// Tulip figure helpers: the fluid palette (linked colour families by field size), theme-aware colour
// lookup, units and a shared tooltip. Uses SubScout's runtime for tokens, units and scheme changes.
import { token, tooltip as ssTooltip, units, UNITS, onSchemeChange, reducedMotion } from "../runtime/js/subscout.js";

// Six size classes per fluid (small -> super-giant). Light: smaller = deeper; dark: smaller = brighter.
// Oil (with NGL and condensate) in green families, gas in brick/amber families; oil is kept darker than
// gas in each class so the two stay apart for colour-blind readers (checked: >= 6.3 dE x100 worst case).
const PAL = {
  light: {
    oil: ["#063215", "#005126", "#00703e", "#1a8f69", "#5eb198", "#9dd5c7"],
    gas: ["#a0412e", "#c35a25", "#dd7610", "#eb9939", "#f2bc79", "#f7ddb7"],
    silhouette: "#8798a6",
  },
  dark: {
    oil: ["#91d993", "#60bc71", "#329d5a", "#067f5c", "#10614d", "#17433b"],
    gas: ["#ffeee8", "#ffcab2", "#ffa663", "#df8b1e", "#af761e", "#7c5d29"],
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
  legendEl.innerHTML = `<div class="tl-legend">` + fam.map(([t, cs]) => `<span class="tl-grp"><b>${t}</b>` +
    cs.map((c) => `<span><i style="background:linear-gradient(90deg,${P.oil[c.idx]} 50%,${P.gas[c.idx]} 50%)"></i>${c.short} <span class="tl-note-inline">${c.range}</span></span>`).join("") + "</span>").join("") +
    `<span class="tl-note-inline">Million boe recoverable. Green: oil, NGL and condensate; orange: gas. Smaller fields are deeper shades.</span></div>`;
}
