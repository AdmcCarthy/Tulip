// The third figure: oil and gas added together, one stream graph, on the same scale (pixels per million Sm³)
// and colours as the pair, so its width can be read against the two graphs above.
import create from "./bulb.js";

export default (el, data, opts = {}) => create(el, data, { ...opts, panels: ["oe"], scaleWith: ["gas", "liq"], autoLabels: true });
