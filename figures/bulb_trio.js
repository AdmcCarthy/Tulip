// Small and medium fields: all of them together, small on its own, medium on its own, side by side. The three share
// one scale, stretched to fill the frame (the bar and the note say by how much against the total). On the total's
// own scale they would be slivers too thin to read, so there is no figure at that scale.
import create from "./bulb.js";

const GROUPS = [
  { title: "Small and medium", short: "Small + medium", classes: [0, 1] },
  { title: "Small", short: "Small", classes: [0] },
  { title: "Medium", short: "Medium", classes: [1] },
];

export default (el, data, opts = {}) => create(el, data, { ...opts, groups: GROUPS, lift: 2, scaleBar: true, scaleNote: "total", autoLabels: true });
