// Tulip figure helpers: the fluid palette (linked colour families by field size), theme-aware colour
// lookup, units and a shared tooltip. Uses SubScout's runtime for tokens, units and scheme changes.
import { token, tooltip as ssTooltip, units, UNITS, onSchemeChange, reducedMotion } from "../runtime/js/subscout.js";

// Six size classes per fluid (small -> super-giant). Light: smaller = paler (cream), the smallest almost
// the white of the seams; dark: smaller = closer to the dark background. Saturated ramps, so giants carry
// the colour and the long tail of small fields stays pale: oil (with NGL and condensate) runs lime to deep
// green, gas runs cream through amber and orange to crimson.
// Hue and lightness both rise with size. Red against green is the weak pair for colour-blind readers
// (deuteranopia: both read olive-brown); the separate columns, the seams and the lightness order carry it.
const PAL = {
  light: {
    oil: ["#f1f3c8", "#cfe6a0", "#9bd27f", "#5fb56b", "#27895a", "#0b5c42"],
    gas: ["#fdf0cc", "#fbd98e", "#f5ab5b", "#e8753f", "#d0453a", "#a8203f"],
    silhouette: "#8798a6",
  },
  dark: {
    oil: ["#1c2a22", "#2c5a3b", "#3e8a4d", "#5fb96b", "#8fe08a", "#d0f79a"],
    gas: ["#2f2420", "#7a4a2a", "#b9692f", "#e8833a", "#f4584a", "#ff5c79"],
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
.tl-flabel{font:600 11.5px var(--ss-font-body);pointer-events:none}
.tl-gyear{font:500 12.5px var(--ss-font-body);fill:var(--ss-text);paint-order:stroke;stroke:var(--ss-surface);stroke-width:5px;stroke-linejoin:round}
.tl-gev{font:400 12px var(--ss-font-body);fill:var(--ss-text-muted)}
.tl-gev b{font-weight:600;fill:var(--ss-text)}
.tl-sea{font:500 15px var(--ss-font-display);fill:var(--ss-text);paint-order:stroke;stroke:var(--ss-surface);stroke-width:3px}
.tl-area{font:600 11.5px var(--ss-font-body);fill:var(--ss-text);paint-order:stroke;stroke:var(--ss-surface);stroke-width:3px}
.tl-hub{font:500 10.5px var(--ss-font-mono);fill:var(--ss-text-muted);paint-order:stroke;stroke:var(--ss-surface);stroke-width:3px}
.tl-year{font:500 15px var(--ss-font-display);fill:var(--ss-text)}
.tl-seas .tl-note:not(.tl-strong){paint-order:stroke;stroke:var(--ss-surface);stroke-width:3px;stroke-linejoin:round}
.tl-maps .tl-year,.tl-maps .tl-note{paint-order:stroke;stroke:var(--ss-surface);stroke-width:3px;stroke-linejoin:round}
.tl-legend{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12px;line-height:1.5;margin:0 0 8px;color:var(--ss-text)}
.tl-legend i{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.tl-legend b{font-weight:600;margin-right:2px}
.tl-legend .tl-grp{display:inline-flex;flex-wrap:wrap;gap:4px 10px;align-items:center}
.tl-note-inline{color:var(--ss-text-muted)}
.tl-maps{display:flex;flex-wrap:wrap;gap:10px}
.tl-legend-compact{font-size:11px;gap:2px 10px;margin-bottom:4px}
.tl-legend-compact .tl-grp{gap:2px 8px}
.tl-legend-compact i{width:10px;height:10px;margin-right:3px}
.tl-ev-y{font:600 12.5px var(--ss-font-mono);fill:var(--ss-text);letter-spacing:.04em}
.tl-ev{font:500 14px var(--ss-font-body);fill:var(--ss-text)}
`;
if (!document.getElementById("tl-css")) {
  const s = document.createElement("style");
  s.id = "tl-css";
  s.textContent = CSS;
  document.head.append(s);
}

/** Size-class legend: two linked families, oil | gas swatch pairs. */
export function classLegend(legendEl, classes, lift = 0) {
  if (!legendEl) return;
  const P = pal();
  // lift: the figure steps these classes up the ramp so pale classes stay visible; the swatches follow
  classes = classes.map((c) => ({ ...c, idx: Math.min(5, c.idx + lift) }));
  const fam = [["Small to large", classes.filter((c) => c.family === 0)], ["Giant and above", classes.filter((c) => c.family === 1)]].filter(([, cs]) => cs.length);
  if (legendEl.clientWidth && legendEl.clientWidth < 560) {
    legendEl.innerHTML = `<div class="tl-legend tl-legend-compact"><span class="tl-grp"><b>Field size</b>` +
      classes.map((c) => `<span><i style="background:linear-gradient(90deg,${P.oil[c.idx]} 50%,${P.gas[c.idx]} 50%)"></i>${c.short === "Super-giant" ? "Super" : c.short}</span>`).join("") +
      `</span><span class="tl-note-inline">small → large; left half oil, right half gas</span></div>`;
    return;
  }
  legendEl.innerHTML = `<div class="tl-legend">` + fam.map(([t, cs]) => `<span class="tl-grp"><b>${t}</b>` +
    cs.map((c) => `<span><i style="background:linear-gradient(90deg,${P.oil[c.idx]} 50%,${P.gas[c.idx]} 50%)"></i>${c.short} <span class="tl-note-inline">${c.range}</span></span>`).join("") + "</span>").join("") +
    `<span class="tl-note-inline">Million boe recoverable. Green: oil, NGL and condensate; red and orange: gas. Smaller fields are paler; the smallest almost vanish into the seams.</span></div>`;
}
