// The third figure: oil and gas added together, one stream graph, same scale and colours as the pair.
import create from "./bulb.js";

export default (el, data, opts = {}) => create(el, data, { ...opts, panels: ["oe"], autoLabels: true });
