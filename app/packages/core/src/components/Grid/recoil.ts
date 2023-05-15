import { atom, selector } from "recoil";

import * as fos from "@fiftyone/state";

export const defaultGridZoom = selector<number>({
  key: "defaultGridZoom",
  get: ({ get }) => get(fos.config)?.gridZoom,
});

export const gridZoom = atom<number>({
  key: "gridZoom",
  default: defaultGridZoom,
});

export const gridZoomRange = atom<[number, number]>({
  key: "gridZoomRange",
  default: [0, 10],
});

export const rowAspectRatioThreshold = selector<number>({
  key: "rowAspectRatioThreshold",
  get: ({ get }) => 11 - Math.max(get(gridZoom), get(gridZoomRange)[0]),
});
