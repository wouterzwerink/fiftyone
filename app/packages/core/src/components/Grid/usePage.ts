import { Get } from "@fiftyone/flashlight/src/state";
import { zoomAspectRatio } from "@fiftyone/looker";
import { getPageQuery } from "@fiftyone/relay";
import { Lookers, LookerStore, samplesPivot } from "@fiftyone/state";
import { MutableRefObject, useRef } from "react";
import { useRecoilCallback } from "recoil";
import { DatasetPageQuery } from "../../../../app/src/pages/datasets/__generated__/DatasetPageQuery.graphql";

const usePage = (
  modal: boolean,
  store: LookerStore<Lookers>
): [MutableRefObject<number>, Get<number>] => {
  const next = useRef(0);
  return [
    next,
    useRecoilCallback(
      ({ snapshot }) =>
        (page: number, set) => {
          const pivot = snapshot.getLoadable(samplesPivot);

          if (pivot.state !== "hasValue" || !pivot.contents) {
            throw new Error("NO");
          }

          const { samples } = pivot.contents;

          if (!samples.edges.length) {
            set({ items: [], nextRequestKey: null });
            return;
          }
          const pivotCursor =
            getPageQuery<DatasetPageQuery>().pageQuery.preloadedQuery.variables
              .samplesCursor;
          const itemData = samples.edges.map(({ node, cursor }) => {
            const data = {
              sample: node.sample,
              aspectRatio: node.aspectRatio,
              cursor,
              urls: Object.fromEntries(
                (node.urls || []).map(({ field, url }) => [field, url])
              ),
            };

            store.samples.set(`${pivotCursor}/${cursor}`, data);
            store.indices.set(next.current, `${pivotCursor}/${cursor}`);
            next.current++;

            return data;
          });

          const items = itemData.map(({ sample, aspectRatio, cursor }) => {
            return {
              id: `${pivotCursor}/${cursor}`,
              aspectRatio: false
                ? zoomAspectRatio(sample, aspectRatio)
                : aspectRatio,
            };
          });
          console.log(items);

          set({
            items,
            nextRequestKey: null,
          });
        },
      [modal]
    ),
  ];
};

export default usePage;
