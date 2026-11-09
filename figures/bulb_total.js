// The third figure: oil and gas added together, one stream graph, same colours as the pair. Drawn narrower than
// the pair's two graphs would add up to (its widest part takes 60% of the frame) so it reads; the bar and the
// note say how the scale compares. The figures after it use this scale.
import create from "./bulb.js";

export default (el, data, opts = {}) => create(el, data, { ...opts, panels: ["oe"], scaleWith: true, scaleBar: true, scaleNote: "pair", autoLabels: true });
