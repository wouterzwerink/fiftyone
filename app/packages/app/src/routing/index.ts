import React from "react";
import { PreloadedQuery } from "react-relay";

import { IndexPageQuery } from "../pages/__generated__/IndexPageQuery.graphql";
import { DatasetPageQuery } from "../pages/datasets/__generated__/DatasetPageQuery.graphql";

export { default as Renderer } from "../Renderer";
export * from "./RouteDefinition";
export * from "./RouterContext";
export * from "./matchPath";
export { default as useRouter } from "./useRouter";
export { default as useRouterContext } from "./useRouterContext";

export type Queries = IndexPageQuery | DatasetPageQuery;

export type Route<T extends Queries> = React.FC<
  React.PropsWithChildren<{
    prepared: PreloadedQuery<T>;
  }>
>;
