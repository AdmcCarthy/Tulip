// Remaining reserves by Sodir quadrant at six snapshot years, one column per sea (North Sea, Norwegian Sea, Barents Sea) and one
// row per year. Each column is that sea's Relief map view in its own projection (scripts/build_seas.py): north up, no join between
// regions, relief to the edge of the frame. Columns are as wide as their view is, all the same height, so every row lines up.
// Sequential slate ramp, distinct from the fluid colours.
import { tok, vol, volShort, unit, tip, scheme } from "./common.js";
import { paintSvg } from "./relief.js";

const TH = [10, 50, 100, 250, 500, 1000];
const RAMP = {
  light: ["#ecf3f8", "#c2d0dc", "#96aec2", "#6f8da5", "#526c82", "#3c4d5b", "#272f35"],
  dark: ["#2b2e31", "#424b52", "#576a78", "#6e8aa0", "#8cabc4", "#b3cce1", "#deeefb"],
};
let uid = 0;

export default function create(el, { seas: S }) {
  el.innerHTML = "";
  const legend = d3.select(el).append("div").attr("class", "tl-legend");
  const svg = d3.select(el).append("svg").attr("class", "tl-seas").style("display", "block").style("width", "100%").style("height", "auto").style("overflow", "hidden").attr("role", "img")
    .attr("aria-label", "Remaining reserves by quadrant in the North Sea, the Norwegian Sea and the Barents Sea at the end of each snapshot year, one row per year");
  let W = 0;
  const unitBox = (s) => ({ type: "Polygon", coordinates: [[[0, 0], [s.w, 0], [s.w, s.h], [0, s.h], [0, 0]]] });

  function draw(width) {
    W = width;
    const cols = RAMP[scheme()];
    const col = (v) => (v > 0 ? cols[d3.bisectRight(TH, v)] : null);
    const narrow = W < 640;
    legend.html(["< 10", "10–50", "50–100", "100–250", "250–500", "500–1,000", "> 1,000"].map((l, i) => `<span><i style="background:${cols[i]}"></i>${l}</span>`).join("") + `<span class='tl-note-inline'>million Sm³ o.e. per quadrant${narrow ? "; the figure in each corner is the sea's total" : ""}</span>`);
    svg.selectAll("*").remove();
    const id = `tl-sea-${++uid}`, gut = narrow ? 0 : 96, gap = narrow ? 5 : 10, head = narrow ? 18 : 26;
    const asp = S.seas.map((s) => s.w / s.h), H = (W - gut - 2 * gap) / d3.sum(asp), rows = S.years.length;
    const totalH = head + rows * (H + gap);
    svg.attr("viewBox", [0, 0, W, totalH]).attr("height", totalH);
    const xs = asp.map((_, j) => gut + d3.sum(asp.slice(0, j)) * H + j * gap);
    const defs = svg.append("defs");
    const shelf = S.years.map((_, r) => d3.sum(S.seas, (s) => d3.sum(s.quads, (q) => q.v[r])));
    S.seas.forEach((sea, j) => {
      const w = asp[j] * H;
      const proj = d3.geoIdentity().reflectY(true).fitExtent([[0, 0], [w, H]], unitBox(sea));
      const path = d3.geoPath(proj);
      svg.append("text").attr("class", "tl-col").attr("x", xs[j] + w / 2).attr("y", head - 8).attr("text-anchor", "middle").text(sea.name);
      // the relief is drawn once per sea and reused by every row
      const base = { features: sea.relief.map((f) => ({ type: "Feature", properties: { kind: f.k, mid: f.mid }, geometry: f.g })), coverage: unitBox(sea) };
      paintSvg(defs.append("g").attr("id", `${id}-${j}`), base, path, { width: w, height: H, seaCap: 500 });
      S.years.forEach((yr, r) => {
        const y0 = head + r * (H + gap);
        const g = svg.append("g").attr("transform", `translate(${xs[j]},${y0})`);
        g.append("use").attr("href", `#${id}-${j}`);
        sea.borders.forEach((b) => g.append("path").datum({ type: "Feature", geometry: b }).attr("d", path).attr("fill", "none").attr("stroke", tok("text-muted")).attr("stroke-width", 0.7).attr("stroke-dasharray", "3 2"));
        g.append("g").selectAll("path").data(sea.quads.filter((q) => q.v[r] > 0)).join("path").attr("d", (q) => path({ type: "Feature", geometry: q.g }))
          .attr("fill", (q) => col(q.v[r])).attr("stroke", tok("text-muted")).attr("stroke-opacity", 0.55).attr("stroke-width", 0.5)
          .on("pointermove", (ev, q) => tip().show(`<b>Quadrant ${q.q}</b> <span class="ss-k">${sea.name}</span><br><span class="ss-k">End of ${yr}</span><br>${vol(q.v[r], 1)} remaining`, ev.clientX, ev.clientY))
          .on("pointerleave", () => tip().hide());
        g.append("rect").attr("width", w).attr("height", H).attr("fill", "none").attr("stroke", tok("border-subtle")).attr("stroke-width", 0.75);
        const tot = d3.sum(sea.quads, (q) => q.v[r]);
        g.append("text").attr("class", "tl-note").attr("x", 6).attr("y", 14).text(tot > 0 ? (narrow ? volShort(tot) : vol(tot)) : narrow ? "–" : "none yet");
        if (narrow && j === 0) g.append("text").attr("class", "tl-year").attr("x", 6).attr("y", 30).text(yr);
        // each view has its own projection, so north is not quite up the page: the arrow shows where it points
        const na = g.append("g").attr("transform", `translate(${w - 13},${narrow ? 14 : 20}) rotate(${sea.north_deg})`);
        na.append("path").attr("d", "M0,-8 L3.5,4 L0,1.5 L-3.5,4 Z").attr("fill", tok("text-muted"));
        if (!narrow) na.append("text").attr("class", "tl-note").attr("y", -11).attr("text-anchor", "middle").text("N");
      });
    });
    if (!narrow) S.years.forEach((yr, r) => {
      const y0 = head + r * (H + gap);
      svg.append("text").attr("class", "tl-year").attr("x", 0).attr("y", y0 + 20).text(yr);
      svg.append("text").attr("class", "tl-note tl-strong").attr("x", 0).attr("y", y0 + 38).text(volShort(shelf[r]));
      svg.append("text").attr("class", "tl-note").attr("x", 0).attr("y", y0 + 51).text(`million ${unit().short}${unit().short === "Sm³" ? " o.e." : ""}`);
      svg.append("text").attr("class", "tl-note").attr("x", 0).attr("y", y0 + 64).text("whole shelf");
    });
  }
  return { draw, repaint() { if (W) draw(W); } };
}
