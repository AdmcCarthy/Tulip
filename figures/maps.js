// Remaining reserves by quadrant at six snapshot years. Conic projection rotated so the shelf runs up
// the panel (north arrow shows the turn); framed on the quadrants that ever held reserves and the
// Norway–Denmark boundary. Sequential slate ramp, distinct from the fluid colours.
import { tok, vol, tip, scheme } from "./common.js";
import { paintSvg } from "./relief.js";

const YEARS = ["1975", "1985", "1995", "2005", "2015", "2025"];
const TH = [10, 50, 100, 250, 500, 1000];
const RAMP = {
  light: ["#ecf3f8", "#c2d0dc", "#96aec2", "#6f8da5", "#526c82", "#3c4d5b", "#272f35"],
  dark: ["#2b2e31", "#424b52", "#576a78", "#6e8aa0", "#8cabc4", "#b3cce1", "#deeefb"],
};
const ANGLE = 18;

export default function create(el, { quads: Q, relief: R, land: LAND, borders: BORDERS }) {
  el.innerHTML = "";
  const legend = d3.select(el).append("div").attr("class", "tl-legend");
  const grid = d3.select(el).append("div").attr("class", "tl-maps");
  let W = 0;
  function draw(width) {
    W = width;
    const cols = RAMP[scheme()];
    const col = (v) => (v > 0 ? cols[d3.bisectRight(TH, v)] : null);
    legend.html(["< 10", "10–50", "50–100", "100–250", "250–500", "500–1,000", "> 1,000"].map((l, i) => `<span><i style="background:${cols[i]}"></i>${l}</span>`).join("") + "<span class='tl-note-inline'>million Sm³ o.e. per quadrant</span>");
    grid.selectAll("*").remove();
    const ncol = W < 520 ? 2 : W < 900 ? 3 : 6;
    const cw = (W - (ncol - 1) * 10) / ncol, ch = Math.round(cw * 1.3);
    const used = Q.features.filter((f) => YEARS.some((y) => (f.properties[y] || 0) > 0));
    const frame = { type: "FeatureCollection", features: [...used, { type: "Feature", geometry: { type: "MultiPoint", coordinates: [[3.0, 56.0], [8.0, 55.6], [10.6, 57.7]] } }] };
    const proj = d3.geoConicConformal().parallels([60, 72]).rotate([-12, 0]).angle(ANGLE).fitExtent([[6, 26], [cw - 6, ch - 4]], frame);
    const path = d3.geoPath(proj);
    YEARS.forEach((yr) => {
      const tot = d3.sum(Q.features, (f) => f.properties[yr] || 0);
      const svg = grid.append("svg").attr("viewBox", [0, 0, cw, ch]).style("width", `${cw}px`).style("height", `${ch}px`).style("overflow", "hidden")
        .attr("role", "img").attr("aria-label", `Remaining reserves by quadrant, end of ${yr}`);
      paintSvg(svg.append("g"), R, path, { width: cw, height: ch, land: LAND, seaCap: 500 });
      svg.append("path").datum(BORDERS).attr("d", path).attr("fill", "none").attr("stroke", tok("text-muted")).attr("stroke-width", 0.7).attr("stroke-dasharray", "3 2");
      svg.append("g").selectAll("path").data(Q.features.filter((f) => (f.properties[yr] || 0) > 0)).join("path").attr("d", path)
        .attr("fill", (f) => col(f.properties[yr])).attr("stroke", tok("text-muted")).attr("stroke-opacity", 0.55).attr("stroke-width", 0.5)
        .on("pointermove", (ev, f) => tip().show(`<b>Quadrant ${f.properties.q}</b><br><span class="ss-k">End of ${yr}</span><br>${vol(f.properties[yr], 1)} remaining`, ev.clientX, ev.clientY))
        .on("pointerleave", () => tip().hide());
      svg.append("text").attr("class", "tl-year").attr("x", 6).attr("y", 16).text(yr);
      svg.append("text").attr("class", "tl-note").attr("x", 6).attr("y", 30).text(vol(tot));
      const na = svg.append("g").attr("transform", `translate(${cw - 14},${20}) rotate(${ANGLE})`);
      na.append("path").attr("d", "M0,-9 L4,5 L0,2 L-4,5 Z").attr("fill", tok("text-muted"));
      na.append("text").attr("class", "tl-note").attr("y", -12).attr("text-anchor", "middle").text("N");
    });
  }
  return { draw, repaint() { if (W) draw(W); } };
}
