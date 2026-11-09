// The main figure: gas (left, warm) and oil, NGL and condensate (right, green) as two linked stream
// graphs on one scale, with the time axis and the story's events in the gutter between them.
import create from "./bulb.js";

export default (el, data, opts = {}) => create(el, data, { ...opts, panels: ["gas", "liq"], gutter: true, autoLabels: true });
