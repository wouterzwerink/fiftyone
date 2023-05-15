import { createResourceGroup } from "@fiftyone/utilities";
import { ConcreteRequest } from "relay-runtime";
import { IndexPageQuery } from "./pages/__generated__/IndexPageQuery.graphql";
import { DatasetPageQuery } from "./pages/datasets/__generated__/DatasetPageQuery.graphql";
import {
  Queries,
  Route,
  RouteDefinition,
  RouteOptions,
  Transitions,
} from "./routing";

const components = createResourceGroup<Route<Queries>>();
const queries = createResourceGroup<ConcreteRequest>();

const makeRouteDefinitions = (routes: {
  "/": Omit<RouteOptions<IndexPageQuery>, "path">;
  "/datasets/:name": Omit<RouteOptions<DatasetPageQuery>, "path">;
}): RouteDefinition<Queries>[] => {
  return Object.entries(routes).map(
    ([path, { component, query, searchParams, transitions }]) => ({
      path,
      component: components(path, component as () => Promise<Route<Queries>>),
      query: queries(path, query),
      searchParams,
      transitions: transitions as Transitions<Queries>,
    })
  );
};

const makeRoutes = () => {
  return makeRouteDefinitions({
    "/": {
      component: () =>
        import("./pages/IndexPage").then((module) => module.default),
      query: () =>
        import("./pages/__generated__/IndexPageQuery.graphql").then(
          (module) => module.default
        ),
      searchParams: {},
    },
    "/datasets/:name": {
      transitions: {
        samplesTransition: (location) => {
          return location.state.cursor;
        },
      },
      component: () =>
        import("./pages/datasets/DatasetPage").then((module) => module.default),
      query: () =>
        import("./pages/datasets/__generated__/DatasetPageQuery.graphql").then(
          (module) => module.default
        ),
      searchParams: {
        view: { name: "savedViewSlug" },
        sampleId: {
          name: "after",
          resolver: (sampleId) => {
            return {
              samplesCursor: sampleId ? `:${sampleId}` : `0:`,
              samplesPage: 40,
            };
          },
        },
      },
    },
  });
};

export default makeRoutes;
