// The bulb: three linked vertical stream graphs (liquids, gas, oil equivalent) on one scale.
// Canvas for the ~1,200 streams (paths built once in data units, placed by matrix; one canvas per state,
// painted ahead in idle time), an SVG
// overlay for axes, labels and hover. State changes cross-fade two stacked canvases (opacity only).
//
// state: { mode: "silhouette" | "colour", focus: [field keys], classes: [size class idx], note: str }
import { pal, shade, tok, vol, volShort, tip, fmt1, parseMonth, fmtMonth, reducedMotion, classLegend, scheme } from "./common.js";

const PANELS = [
  { key: "liq", title: "Oil, NGL & condensate", short: "Liquids" },
  { key: "gas", title: "Gas", short: "Gas" },
  { key: "oe", title: "Oil equivalent", short: "Oil eq." },
];

function gaussian(v, sig) {
  const rad = Math.ceil(sig * 3), ker = [];
  for (let k = -rad; k <= rad; k++) ker.push(Math.exp(-(k * k) / (2 * sig * sig)));
  const out = new Float32Array(v.length);
  for (let t = 0; t < v.length; t++) {
    let s = 0, w = 0;
    for (let k = -rad; k <= rad; k++) { const j = t + k; if (j < 0 || j >= v.length) continue; s += v[j] * ker[k + rad]; w += ker[k + rad]; }
    out[t] = s / w < 0.005 ? 0 : s / w;
  }
  return out;
}

export default function create(el, { bulb: B }, opts = {}) {
  const drawLegend = () => classLegend(opts.legendEl, B.classes);
  drawLegend();
  const n = B.dates.length;
  const dates = B.dates.map(parseMonth);
  const F = B.fields.map((f) => {
    const oe = f.liq.map((v, t) => v + f.gas[t]);
    return { ...f, raw: { liq: f.liq, gas: f.gas, oe }, sm: { liq: gaussian(f.liq, B.smooth_sigma), gas: gaussian(f.gas, B.smooth_sigma), oe: gaussian(oe, B.smooth_sigma) } };
  });
  // oldest at the centre, younger alternating left and right
  const order = [];
  [...F.keys()].sort((a, b) => F[a].entry - F[b].entry).forEach((i, k) => (k % 2 ? order.unshift(i) : order.push(i)));
  const LAY = Object.fromEntries(PANELS.map(({ key }) => {
    const sers = order.filter((i) => F[i].raw[key].some((v) => v > 0));
    const x0 = {}, x1 = {}, tot = new Float32Array(n);
    sers.forEach((i) => { x0[i] = new Float32Array(n); x1[i] = new Float32Array(n); });
    for (let t = 0; t < n; t++) {
      let s = 0; for (const i of sers) s += F[i].sm[key][t];
      tot[t] = s; let c = -s / 2;
      for (const i of sers) { x0[i][t] = c; c += F[i].sm[key][t]; x1[i][t] = c; }
    }
    return [key, { sers, x0, x1, tot }];
  }));
  const RAW = Object.fromEntries(PANELS.map(({ key }) => [key, dates.map((_, t) => d3.sum(F, (f) => f.raw[key][t]))]));
  const peakRaw = Object.fromEntries(PANELS.map(({ key }) => [key, key === "oe" ? B.peak : d3.max(RAW[key])]));
  const maxW = PANELS.map(({ key }) => d3.max(LAY[key].tot));

  el.innerHTML = "";
  el.classList.add("tl-bulb");
  const wrap = d3.select(el).append("div").style("position", "relative");
  const layer = wrap.append("div").style("position", "absolute").style("left", 0).style("top", 0).node();
  const svg = wrap.append("svg").style("position", "relative").style("display", "block").style("width", "100%").style("height", "auto");
  let geo = null, cur = { mode: "colour" }, shown = null, idleQ = null;
  // One canvas per state, painted ahead in idle time: a step only cross-fades opacity (compositor work).
  const cache = new Map();
  const keyOf = (st) => JSON.stringify([st.mode ?? "colour", st.focus ?? [], st.classes ?? []]);
  function entry(st) {
    const k = keyOf(st);
    if (!cache.has(k)) {
      const c = document.createElement("canvas");
      c.style.cssText = "position:absolute;left:0;top:0;opacity:0;pointer-events:none;transition:opacity 600ms ease";
      layer.append(c);
      cache.set(k, { c, W: 0, sch: null });
    }
    return cache.get(k);
  }
  function ensure(st) {
    const e = entry(st);
    if (e.W !== geo.W || e.sch !== scheme()) { paint(e.c, st); e.W = geo.W; e.sch = scheme(); }
    return e;
  }
  function prepareAhead() {
    if (idleQ) return;
    const todo = (opts.states ?? []).map((st) => ({ mode: "colour", ...st }));
    const step = () => {
      const st = todo.shift();
      if (!st) { idleQ = null; return; }
      ensure(st);
      idleQ = (window.requestIdleCallback ?? ((f) => setTimeout(f, 80)))(step, { timeout: 1500 });
    };
    idleQ = (window.requestIdleCallback ?? ((f) => setTimeout(f, 80)))(step, { timeout: 1500 });
  }

  // Paths in data units (x: MSm³ offset from the panel centre, y: decimal year) built once; each paint
  // places them with a matrix, so a resize or a state change never rebuilds geometry.
  const yr = dates.map((d) => d.getFullYear() + (d - new Date(d.getFullYear(), 0, 1)) / 3.15576e10);
  const def = (v, t) => v[t] > 0 || (t + 1 < n && v[t + 1] > 0) || (t > 0 && v[t - 1] > 0);
  const NORM = PANELS.map(({ key }) => {
    const L = LAY[key];
    const sers = L.sers.map((i) => {
      const p = new Path2D();
      d3.area().curve(d3.curveBasis).context(p).defined((_, t) => def(F[i].sm[key], t)).y((_, t) => yr[t]).x0((_, t) => L.x0[i][t]).x1((_, t) => L.x1[i][t])(dates);
      return { i, p };
    });
    const seams = new Path2D();
    sers.forEach((s) => seams.addPath(s.p));
    const sil = new Path2D();
    d3.area().curve(d3.curveBasis).context(sil).defined((_, t) => def(L.tot, t)).y((_, t) => yr[t]).x0((_, t) => -L.tot[t] / 2).x1((_, t) => L.tot[t] / 2)(dates);
    return { sers, seams, sil };
  });

  function build(W) {
    const narrow = W < 560, mL = narrow ? 4 : 12, mR = narrow ? 30 : 46, mT = 44, mB = 8, gap = narrow ? 6 : 16;
    const vh = window.innerHeight || 800;
    // 10% shorter than v0.2, and never taller than the room left by the figure's header, notes and top bar
    const fig = el.closest(".ss-figure"), other = fig ? fig.offsetHeight - el.offsetHeight : 0;
    const room = narrow ? Infinity : vh - 64 - other;
    const H = Math.round(Math.max(narrow ? 270 : 340, Math.min(W * 1.17, vh * (narrow ? 0.36 : 0.65), room, 990)));
    const k = (W - mL - mR - 2 * gap) / d3.sum(maxW);
    let acc = mL;
    const cx = maxW.map((m) => { const c = acc + (m * k) / 2; acc += m * k + gap; return c; });
    const y = d3.scaleTime([new Date(B.axis_start, 0, 1), new Date(B.axis_end, 11, 31)], [H - mB, mT]);
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    // decimal year -> pixel row: linear, from two points of the time scale
    const y0 = y(new Date(2000, 0, 1)), sy = y(new Date(2010, 0, 1)) - y0;
    const mats = cx.map((c) => new DOMMatrix([k * dpr, 0, 0, (sy / 10) * dpr, c * dpr, (y0 - 2000 * (sy / 10)) * dpr]));
    return { W, H, narrow, mL, mR, mT, mB, k, cx, y, dpr, mats };
  }

  function paint(c, state) {
    const g = geo, ctx = c.getContext("2d");
    if (c.width !== g.W * g.dpr || c.height !== g.H * g.dpr) { c.width = g.W * g.dpr; c.height = g.H * g.dpr; }
    ctx.clearRect(0, 0, c.width, c.height);
    const P = pal(), bg = tok("surface");
    if (state.mode === "silhouette") {
      NORM.forEach((p, j) => { const q = new Path2D(); q.addPath(p.sil, g.mats[j]); ctx.fillStyle = P.silhouette; ctx.fill(q); });
      return;
    }
    const focus = state.focus?.length ? new Set(state.focus) : null;
    const cls = state.classes?.length ? new Set(state.classes) : null;
    const on = (f) => (!focus || focus.has(f.key)) && (!cls || cls.has(f.cls));
    NORM.forEach((p, j) => {
      const key = PANELS[j].key, groups = new Map();
      for (const s of p.sers) {
        const f = F[s.i], colour = key === "oe" ? shade(f.dom, f.cls) : shade(key, f.cls), id = `${colour}|${on(f) ? 1 : 0}`;
        if (!groups.has(id)) groups.set(id, { colour, alpha: on(f) ? 1 : 0.2, path: new Path2D() });
        groups.get(id).path.addPath(s.p, g.mats[j]);
      }
      for (const gr of groups.values()) { ctx.globalAlpha = gr.alpha; ctx.fillStyle = gr.colour; ctx.fill(gr.path); }
      const seams = new Path2D(); seams.addPath(p.seams, g.mats[j]);
      ctx.strokeStyle = bg; ctx.lineJoin = "round";
      ctx.globalAlpha = 0.22; ctx.lineWidth = 1.2 * g.dpr; ctx.stroke(seams);
      ctx.globalAlpha = 1; ctx.lineWidth = (g.narrow ? 0.3 : 0.45) * g.dpr; ctx.stroke(seams);
    });
    ctx.globalAlpha = 1;
  }

  function overlay(state) {
    const g = geo, { W, H, y, cx, k, mL, mR, mT } = g;
    svg.attr("viewBox", [0, 0, W, H]).attr("role", "img")
      .attr("aria-label", "Three stream graphs of remaining reserves per field, liquids, gas and oil equivalent, from 1971 to today, time running up");
    svg.selectAll("*").remove();
    const today = dates[n - 1], yNow = y(today), x1 = W - mR + 30;
    svg.append("rect").attr("x", mL).attr("width", x1 - mL).attr("y", mT).attr("height", yNow - mT).attr("fill", tok("surface-raised")).attr("opacity", 0.6);
    svg.append("text").attr("class", "tl-note").attr("x", mL + 4).attr("y", mT + 13).text(`Next ten years, to ${B.axis_end}`);
    const yrs = d3.range(1970, B.axis_end + 1, 10).map((v) => new Date(v, 0, 1));
    const ax = svg.append("g");
    ax.selectAll("line").data(yrs).join("line").attr("x1", mL).attr("x2", x1).attr("y1", y).attr("y2", y).attr("stroke", tok("grid")).attr("stroke-dasharray", "1 3");
    ax.selectAll("text").data(yrs).join("text").attr("class", "tl-axis").attr("x", W - 2).attr("y", y).attr("dy", "0.35em").attr("text-anchor", "end").text((d) => d.getFullYear());
    svg.append("line").attr("x1", mL).attr("x2", x1).attr("y1", yNow).attr("y2", yNow).attr("stroke", tok("text")).attr("stroke-width", 1);
    svg.append("text").attr("class", "tl-axis tl-strong").attr("x", W - 2).attr("y", yNow).attr("dy", "0.35em").attr("text-anchor", "end").text("Today");
    PANELS.forEach((p, j) => {
      svg.append("text").attr("class", "tl-col").attr("x", cx[j]).attr("y", 14).attr("text-anchor", "middle").text(g.narrow ? p.short : p.title);
      svg.append("text").attr("class", "tl-note").attr("x", cx[j]).attr("y", 29).attr("text-anchor", "middle").text(`peak ${volShort(peakRaw[p.key])}`);
    });
    // found but not sanctioned: placeholder width at today in the oil-equivalent column
    const pw = (RAW.oe[n - 1] + B.pending) * k;
    const pat = svg.append("defs").append("pattern").attr("id", "tl-hatch").attr("patternUnits", "userSpaceOnUse").attr("width", 5).attr("height", 5).attr("patternTransform", "rotate(45)");
    pat.append("rect").attr("width", 1).attr("height", 5).attr("fill", tok("text-muted"));
    svg.append("rect").attr("x", cx[2] - pw / 2).attr("width", pw).attr("y", yNow - 11).attr("height", 8).attr("fill", "url(#tl-hatch)").attr("stroke", tok("text-muted")).attr("stroke-width", 0.6);
    svg.append("text").attr("class", "tl-note").attr("x", cx[2]).attr("y", yNow - 16).attr("text-anchor", "middle").text(g.narrow ? "not yet sanctioned" : `+${volShort(B.pending)} found, not yet sanctioned`);
    if (state.mode === "silhouette") {
      const t = d3.maxIndex(RAW.oe);
      svg.append("text").attr("class", "tl-big").attr("x", cx[2]).attr("y", y(dates[t])).attr("text-anchor", "middle").attr("dy", "0.35em").text(vol(B.peak));
      return;
    }
    // labels for focused fields, and their discovery year in the oil-equivalent column
    const keys = state.focus ?? [];
    keys.forEach((key) => {
      const i = F.findIndex((f) => f.key === key);
      if (i < 0) return;
      const f = F[i];
      PANELS.forEach((p, j) => {
        const L = LAY[p.key];
        if (!(i in L.x0)) return;
        const tl = Math.min(n - 1, d3.maxIndex(f.sm[p.key]) + 2), w = (L.x1[i][tl] - L.x0[i][tl]) * k;
        if (w < 22 && p.key !== "oe") return;
        svg.append("text").attr("class", "tl-label").attr("x", cx[j] + ((L.x0[i][tl] + L.x1[i][tl]) / 2) * k).attr("y", y(dates[tl])).attr("dy", "0.35em").attr("text-anchor", "middle").text(f.name);
        if (p.key === "oe" && f.discovered && keys.length <= 2) {
          const te = f.entry, xe = cx[j] + ((L.x0[i][te + 2] + L.x1[i][te + 2]) / 2) * k, yd = y(new Date(f.discovered, 6, 1));
          svg.append("line").attr("x1", xe).attr("x2", xe).attr("y1", yd).attr("y2", y(dates[te])).attr("stroke", tok("text")).attr("stroke-dasharray", "1.5 2.5");
          svg.append("circle").attr("cx", xe).attr("cy", yd).attr("r", 2.6).attr("fill", tok("surface")).attr("stroke", tok("text")).attr("stroke-width", 1.2);
          svg.append("text").attr("class", "tl-found").attr("x", xe + 6).attr("y", yd).attr("dy", "0.35em").text(`found ${f.discovered}`);
        }
      });
    });
    // hover
    const hov = svg.append("g").attr("pointer-events", "none");
    const hl = svg.append("line").attr("stroke", tok("text")).attr("stroke-width", 0.75).attr("stroke-dasharray", "2 2").attr("opacity", 0);
    svg.on("pointermove", (ev) => {
      const [px, py] = d3.pointer(ev);
      if (py < yNow || py > H) { tip().hide(); hl.attr("opacity", 0); hov.selectAll("*").remove(); return; }
      const t = Math.max(0, Math.min(n - 1, d3.bisectLeft(dates, y.invert(py))));
      hl.attr("x1", mL).attr("x2", x1).attr("y1", y(dates[t])).attr("y2", y(dates[t])).attr("opacity", 1);
      let hit = null;
      PANELS.forEach((p, j) => { const L = LAY[p.key], v = (px - cx[j]) / k; for (const i of L.sers) if (v >= L.x0[i][t] && v <= L.x1[i][t] && L.x1[i][t] > L.x0[i][t]) { hit = i; break; } });
      hov.selectAll("*").remove();
      let html = `<b>${fmtMonth(dates[t])}</b><br><span class="ss-k">All fields, remaining</span><br>Liquids ${vol(RAW.liq[t])}<br>Gas ${vol(RAW.gas[t])}<br><b>Total ${vol(RAW.oe[t])}</b>`;
      if (hit != null) {
        const f = F[hit], lv = f.raw.liq[t], gv = f.raw.gas[t];
        PANELS.forEach((p, j) => {
          const L = LAY[p.key]; if (!(hit in L.x0)) return;
          hov.append("path").attr("fill", "none").attr("stroke", tok("text")).attr("stroke-width", 1.4)
            .attr("d", d3.area().curve(d3.curveBasis).defined((_, tt) => f.sm[p.key][tt] > 0 || (tt + 1 < n && f.sm[p.key][tt + 1] > 0)).y((_, tt) => y(dates[tt]))
              .x0((_, tt) => cx[j] + L.x0[hit][tt] * k).x1((_, tt) => cx[j] + L.x1[hit][tt] * k)(dates));
        });
        const c = B.classes[f.cls];
        html = `<b>${f.name}</b>${f.cross_border ? " <span class='ss-k'>(Norwegian share)</span>" : ""}<br><span class="ss-k">${f.area}${f.discovered ? ` · found ${f.discovered}` : ""}${f.first_prod ? ` · on stream ${f.first_prod.slice(0, 4)}` : ""}${f.status === "Shut down" ? " · shut down" : ""}</span>
          <br><span class="ss-k">${fmtMonth(dates[t])}, remaining</span><br>Liquids ${vol(lv, 1)}<br>Gas ${vol(gv, 1)}<br><b>Total ${vol(lv + gv, 1)}</b> <span class="ss-k">(${d3.format(".1%")((lv + gv) / RAW.oe[t])} of the shelf)</span>
          <br><span class="ss-k">${c.short}, ${c.range} MMboe recoverable</span>`;
      }
      tip().show(html, ev.clientX, ev.clientY);
    }).on("pointerleave", () => { tip().hide(); hl.attr("opacity", 0); hov.selectAll("*").remove(); });
  }

  function render(W, state, animate) {
    if (!geo || Math.abs(W / geo.W - 1) > 0.2) geo = build(W); // small resizes scale the bitmaps instead
    const sc = W / geo.W;
    const e = ensure(state);
    const dur = animate && !reducedMotion() ? (cur.mode === "silhouette" && state.mode !== "silhouette" ? 1600 : 600) : 0;
    cache.forEach((x) => {
      x.c.style.width = `${W}px`; x.c.style.height = `${geo.H * sc}px`;
      x.c.style.transitionDuration = `${dur}ms`;
      x.c.style.opacity = x === e ? 1 : 0;
    });
    shown = e;
    cur = state;
    overlay(state);
    prepareAhead();
  }

  return {
    draw(W, state = {}, { animate = false } = {}) { render(W, { mode: "colour", ...state }, animate); },
    repaint() { drawLegend(); if (geo) { cache.forEach((x) => (x.W = 0)); render(geo.W, cur, false); } },
  };
}
