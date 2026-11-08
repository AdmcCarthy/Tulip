// Creaming curve: each field's recoverable volume against its discovery year (log scale).
import { shade, tok, vol, tip, classLegend } from "./common.js";

export default function create(el, { bulb: B }, opts = {}) {
  const drawLegend = () => classLegend(opts.legendEl, B.classes);
  drawLegend();
  const data = B.fields.filter((f) => f.discovered && f.rec_liq + f.rec_gas > 0);
  el.innerHTML = "";
  const svg = d3.select(el).append("svg").style("display", "block").style("width", "100%");
  let W = 0;
  function draw(width) {
    W = width;
    const H = opts.export ? Math.round(opts.height()) : Math.round(Math.max(280, Math.min(W * 0.5, 440))), m = { t: 18, r: 14, b: 26, l: 46 };
    svg.attr("viewBox", [0, 0, W, H]).attr("height", H).attr("role", "img").attr("aria-label", "Scatter of field size against discovery year, log scale");
    svg.selectAll("*").remove();
    const x = d3.scaleLinear([1965, 2026], [m.l, W - m.r]);
    const y = d3.scaleLog([0.05, 2500], [H - m.b, m.t]);
    const g = svg.append("g");
    [0.1, 1, 10, 100, 1000].forEach((v) => {
      g.append("line").attr("x1", m.l).attr("x2", W - m.r).attr("y1", y(v)).attr("y2", y(v)).attr("stroke", tok("grid"));
      g.append("text").attr("class", "tl-axis").attr("x", m.l - 6).attr("y", y(v)).attr("dy", "0.35em").attr("text-anchor", "end").text(d3.format(",")(v));
    });
    // giant threshold (500 MMboe)
    const gy = y(500 / 6.29);
    g.append("line").attr("x1", m.l).attr("x2", W - m.r).attr("y1", gy).attr("y2", gy).attr("stroke", tok("text-muted")).attr("stroke-dasharray", "4 3");
    g.append("text").attr("class", "tl-note").attr("x", W - m.r).attr("y", gy - 5).attr("text-anchor", "end").text("giant: 500 million boe");
    d3.range(1970, 2030, 10).forEach((v) => g.append("text").attr("class", "tl-axis").attr("x", x(v)).attr("y", H - 6).attr("text-anchor", "middle").text(v));
    g.append("text").attr("class", "tl-note").attr("x", m.l).attr("y", 10).text("Recoverable, million Sm³ o.e.");
    svg.append("g").selectAll("circle").data(data).join("circle")
      .attr("cx", (d) => x(d.discovered)).attr("cy", (d) => y(d.rec_liq + d.rec_gas)).attr("r", W < 560 ? 3.6 : 4.6)
      .attr("fill", (d) => shade(d.dom, d.cls)).attr("stroke", (d) => (d.cls === 0 ? tok("text-muted") : tok("surface"))).attr("stroke-width", (d) => (d.cls === 0 ? 0.7 : 1.4))
      .on("pointermove", (ev, d) => tip().show(`<b>${d.name}</b><br><span class="ss-k">${d.area} · found ${d.discovered}</span><br>Recoverable ${vol(d.rec_liq + d.rec_gas)}<br><span class="ss-k">${B.classes[d.cls].short}, mainly ${d.dom === "gas" ? "gas" : "oil and liquids"}</span>`, ev.clientX, ev.clientY))
      .on("pointerleave", () => tip().hide());
    data.filter((d) => d.rec_liq + d.rec_gas > (W < 560 ? 500 : 330) && d.name !== "Gullfaks").forEach((d) =>
      svg.append("text").attr("class", "tl-label").attr("x", x(d.discovered) + 7).attr("y", y(d.rec_liq + d.rec_gas)).attr("dy", "0.35em").text(d.name));
  }
  return { draw, repaint() { drawLegend(); if (W) draw(W); } };
}
