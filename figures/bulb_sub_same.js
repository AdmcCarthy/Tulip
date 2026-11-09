// The shelf without its giants on the scale of the total (and of the gas and oil pair): the outline is the
// whole shelf, the colour is what the fields under 500 MMboe held.
import create from "./bulb.js";

export default (el, data, opts = {}) => create(el, data, { ...opts, panels: ["oe"], classes: [0, 1, 2], lift: 2, ghost: true, scaleWith: true, scaleBar: true, autoLabels: true });
