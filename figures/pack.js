// Circle packing: sea -> area -> hub -> field, sized by volume. Same colours as the bulb.
// state: { t: "rec" | "YYYY-MM" | "now", focus: "area:Tampen" | "sea:North Sea" | null }
import { shade, tok, vol, tip, fmtMonth, parseMonth, reducedMotion, classLegend } from "./common.js";

const SEA = { "North Sea": 0, "Norwegian Sea": 1, "Barents Sea": 2 };

export default function create(el, { bulb: B }, opts = {}) {
  const drawLegend = () => classLegend(opts.legendEl, B.classes);
  drawLegend();
  const F = B.fields;
  const title = (k) => B.hub_names[k] ?? k.split(" ").map((w) => w[0] + w.slice(1).toLowerCase()).join(" ");
  el.innerHTML = "";
  const svg = d3.select(el).append("svg").style("display", "block").style("width", "100%").style("overflow", "hidden");
  let W = 0, H = 0, root = null, view = null, focus = null, cur = {};
  const ti = (t) => (t === "rec" || t == null ? null : t === "now" ? B.dates.length - 1 : B.dates.indexOf(t));

  function layout(state) {
    const t = ti(state.t);
    const val = (f) => (t == null ? f.rec_liq + f.rec_gas : f.liq[t] + f.gas[t]);
    const g = d3.group(F, (f) => f.sea, (f) => f.area, (f) => f.hub);
    const hubNode = ([hub, fs]) => (fs.length === 1 ? { id: fs[0].key, name: fs[0].name, f: fs[0] }
      : { id: `hub:${hub}`, name: `${title(hub)} hub`, kind: "hub", children: fs.map((f) => ({ id: f.key, name: f.name, f })) });
    const data = { id: "NCS", children: [...g].sort((a, b) => SEA[a[0]] - SEA[b[0]]).map(([sea, areas]) => ({
      id: `sea:${sea}`, name: sea, kind: "sea",
      children: [...areas].map(([area, hubs]) => ({ id: `area:${area}`, name: area, kind: "area", children: [...hubs].map(hubNode) })) })) };
    return d3.pack().size([W, H]).padding((d) => [14, 7, 4, 1.5][Math.min(d.depth, 3)])(
      d3.hierarchy(data).sum((d) => (d.f ? Math.max(val(d.f), 0) : 0)).sort((a, b) => b.value - a.value));
  }

  function draw(width, state = {}, { animate = false } = {}) {
    state = { t: "rec", focus: null, ...state };
    const resized = width !== W;
    W = width; H = Math.round(W < 560 ? Math.max(210, Math.min(W * 0.85, (window.innerHeight || 800) * 0.31)) : Math.max(360, Math.min(W * 0.85, (window.innerHeight || 800) * 0.72)));
    svg.attr("viewBox", [0, 0, W, H]).attr("height", H).attr("role", "img").attr("aria-label", "Circle packing of fields grouped by sea, area and hub");
    const prev = new Map();
    if (root && !resized) svg.selectAll("circle.n").each(function (d) { prev.set(d.data.id, [+this.getAttribute("cx"), +this.getAttribute("cy"), +this.getAttribute("r")]); });
    root = layout(state);
    cur = state;
    const nodes = root.descendants().filter((d) => d.depth > 0 && d.r > 0.2);
    const target = (state.focus && nodes.find((d) => d.data.id === state.focus)) || root;
    focus = target;
    view = [target.x, target.y, target.r * (target === root ? 2 : 2.1)];
    const fill = (d) => (d.data.f ? shade(d.data.f.dom, d.data.f.cls) : d.data.kind === "sea" ? tok("surface-raised") : d.data.kind === "area" ? tok("canvas") : "none");
    const circ = svg.selectAll("circle.n").data(nodes, (d) => d.data.id).join("circle").attr("class", "n")
      .attr("fill", fill).attr("fill-opacity", (d) => (d.data.kind === "sea" ? 0.7 : d.data.kind === "area" ? 0.8 : 1))
      .attr("stroke", (d) => (d.data.f ? tok("surface") : tok("text-muted"))).attr("stroke-width", (d) => (d.data.f ? 0.6 : d.data.kind === "sea" ? 1 : 0.8))
      .attr("stroke-dasharray", (d) => (d.data.kind === "hub" ? "2 2" : null)).style("cursor", (d) => (d.children ? "zoom-in" : "default"));
    const lab = svg.selectAll("g.lab").data([0]).join("g").attr("class", "lab").attr("pointer-events", "none").raise();
    const pos = (d, v) => { const kk = W / v[2]; return [(d.x - v[0]) * kk + W / 2, (d.y - v[1]) * kk + H / 2, d.r * kk]; };
    const place = (v) => circ.each(function (d) { const [x, y, r] = pos(d, v); this.setAttribute("cx", x); this.setAttribute("cy", y); this.setAttribute("r", r); });
    function labels() {
      lab.selectAll("*").remove();
      nodes.forEach((d) => {
        const [x, y, r] = pos(d, view), k = d.data.kind;
        if (k === "sea" && (focus === root || focus === d)) lab.append("text").attr("class", "tl-sea").attr("x", x).attr("y", y - r + 20).attr("text-anchor", "middle").text(d.data.name);
        else if (k === "area" && r > 28 && (focus === root || focus === d || focus === d.parent)) lab.append("text").attr("class", "tl-area").attr("x", x).attr("y", y - r + 13).attr("text-anchor", "middle").text(d.data.name);
        else if (k === "hub" && focus !== root && r > 30) lab.append("text").attr("class", "tl-hub").attr("x", x).attr("y", y - r + 11).attr("text-anchor", "middle").text(d.data.name);
        else if (d.data.f && r > (focus === root ? 22 : 14)) lab.append("text").attr("class", "tl-label").attr("x", x).attr("y", y).attr("dy", "0.35em").attr("text-anchor", "middle").style("font-size", r > 40 ? "12px" : "10.5px").text(d.data.name);
      });
    }
    const dur = animate && !reducedMotion() ? 900 : 0;
    if (dur && prev.size) {
      lab.selectAll("*").remove();
      circ.each(function (d) { const p = prev.get(d.data.id); const [x, y] = pos(d, view); if (p) { this.setAttribute("cx", p[0]); this.setAttribute("cy", p[1]); this.setAttribute("r", p[2]); } else { this.setAttribute("cx", x); this.setAttribute("cy", y); this.setAttribute("r", 0); } });
      circ.transition().duration(dur).ease(d3.easeCubicInOut).attr("cx", (d) => pos(d, view)[0]).attr("cy", (d) => pos(d, view)[1]).attr("r", (d) => pos(d, view)[2])
        .end().then(labels).catch(() => {});
    } else { place(view); labels(); }

    function zoom(d) {
      focus = d; lab.selectAll("*").remove();
      const i = d3.interpolateZoom(view, [d.x, d.y, d.r * (d === root ? 2 : 2.1)]);
      svg.transition().duration(reducedMotion() ? 0 : 750).tween("zoom", () => (tt) => { view = i(tt); place(view); }).end().then(labels).catch(() => {});
    }
    circ.on("click", (ev, d) => { ev.stopPropagation(); const z = d.children ? d : d.parent; if (z && focus !== z) zoom(z); });
    svg.on("click", () => { if (focus !== root) zoom(root); });
    const t = ti(state.t);
    circ.on("pointermove", (ev, d) => {
      const liq = d3.sum(d.leaves(), (l) => (l.data.f ? (t == null ? l.data.f.rec_liq : l.data.f.liq[t]) : 0)), v = d.value;
      const when = t == null ? "Recoverable, all time" : `Left, ${fmtMonth(parseMonth(B.dates[t]))}`;
      let html = `<b>${d.data.name}</b>`;
      if (d.data.f) { const f = d.data.f; html += `<br><span class="ss-k">${f.area} · ${f.hub !== f.key ? `tied back to ${title(f.hub)}` : "own facilities"}${f.discovered ? ` · found ${f.discovered}` : ""}</span>`; }
      else html += `<br><span class="ss-k">${d.leaves().filter((l) => l.value > 0).length} fields</span>`;
      html += `<br><span class="ss-k">${when}</span><br>Liquids ${vol(liq)}<br>Gas ${vol(v - liq)}<br><b>Total ${vol(v)}</b>`;
      if (d.data.f) { const c = B.classes[d.data.f.cls]; html += `<br><span class="ss-k">${c.short}, ${c.range} MMboe</span>`; }
      tip().show(html, ev.clientX, ev.clientY);
    }).on("pointerleave", () => tip().hide());
  }

  return { draw, repaint() { drawLegend(); if (W) { const w = W; W = 0; draw(w, cur); } } };
}
