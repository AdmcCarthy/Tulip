// The shelf without its giants (fields under 500 MMboe), oil and gas added, on a scale stretched to fill the
// frame so the small, medium and large fields' own shape and growth can be read. A scale bar says how far.
import create from "./bulb.js";

export default (el, data, opts = {}) => create(el, data, { ...opts, panels: ["oe"], classes: [0, 1, 2], lift: 2, scaleNote: true, autoLabels: true });
