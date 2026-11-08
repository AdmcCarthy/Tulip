// Relief base map for the Wildcat maps: stacked land and sea-floor polygons (scripts/build_relief_base.py, lon/lat) painted in
// Relief's Detuned style: land tints at half strength (boreal ramp), the sea floor on a linear shelf ramp, no hillshade, no contours.
// Features arrive sea first, then land, each in ascending `mid` (m); a feature takes the colour of the band it opens.
import { detunedStyle, rampAt } from "./relief_palette.js";
import { scheme } from "./common.js";

// Context strength: data sits on top of this base, so the sea uses only the first part of Relief's depth ramp (the deepest water is
// the 22 % tone, not the full indigo) and the depth steps stay readable without competing with the marks.
const SEA_SPAN = 0.22;
let clipId = 0;
// `seaCap` (m) is the depth that takes the deepest tone: Relief's 1,300 m shelf scale by default, 500 m where the base is joined from
// several regions, so the deep water beyond the shelf edge is one tone that continues past a region's edge.
const fills = (base, seaCap) => {
  const st = detunedStyle(scheme()), cap = seaCap ?? st.seaMax;
  return base.features.map((f) => ({ f, fill: f.properties.kind === "sea" ? rampAt(st.sea, SEA_SPAN * Math.min(1, f.properties.mid / cap) * (cap / st.seaMax)) : rampAt(st.zones.boreal, f.properties.mid / st.landMax) }));
};

// SVG: paint into selection `g`, clipped to the area Relief covers; `path` is a d3.geoPath. Where Relief has no region (the shelf map
// spans three) `under` = { width, height, land } lays a flat shelf-depth sea and the plain land outline beneath, so the frame has no hole.
export function paintSvg(g, base, path, under) {
  if (under) {
    const st = detunedStyle(scheme());
    g.append("rect").attr("width", under.width).attr("height", under.height).attr("fill", rampAt(st.sea, (SEA_SPAN * under.seaCap) / st.seaMax));
    if (under.land) g.append("path").attr("d", path(under.land)).attr("fill", rampAt(st.zones.boreal, 0));
  }
  const id = `wc-relief-${++clipId}`;
  g.append("clipPath").attr("id", id).append("path").attr("d", path(base.coverage));
  const layer = g.append("g").attr("clip-path", `url(#${id})`);
  fills(base, under?.seaCap).forEach(({ f, fill }) => layer.append("path").attr("d", path(f)).attr("fill", fill).attr("fill-rule", "evenodd"));
}

// Canvas: `path` is a d3.geoPath bound to `ctx`.
export function paintCanvas(ctx, base, path) {
  ctx.save();
  ctx.beginPath(); path(base.coverage); ctx.clip();
  fills(base).forEach(({ f, fill }) => { ctx.beginPath(); path(f); ctx.fillStyle = fill; ctx.fill("evenodd"); });
  ctx.restore();
}
