// Small and medium fields: all of them together, small on its own, medium on its own, side by side. The three share
// one scale; `stretched` blows it up to fill the frame (the bar and the note say by how much), otherwise it is the
// scale of the total, so the graphs show how little of the shelf these fields are.
import create from "./bulb.js";

const GROUPS = [
  { title: "Small and medium", short: "Small + medium", classes: [0, 1] },
  { title: "Small", short: "Small", classes: [0] },
  { title: "Medium", short: "Medium", classes: [1] },
];

export const same = (el, data, opts = {}) => create(el, data, { ...opts, groups: GROUPS, lift: 2, scaleWith: true, scaleBar: true, autoLabels: true });
export const stretched = (el, data, opts = {}) => create(el, data, { ...opts, groups: GROUPS, lift: 2, scaleBar: true, scaleNote: "total", autoLabels: true });
