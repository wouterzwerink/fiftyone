import { LocationState } from "@fiftyone/relay";
import { Resource } from "@fiftyone/utilities";
import { Location } from "history";
import { ConcreteRequest, OperationType, VariablesOf } from "relay-runtime";
import { Queries, Route } from ".";

export interface FiftyOneLocation extends Location {
  state: LocationState;
}

export interface ParameterResolver<T extends OperationType> {
  name: string;
  resolver?: (value: string | null) => Partial<VariablesOf<T>>;
}

export interface ParameterResolvers<T extends OperationType> {
  [key: string]: ParameterResolver<T>;
}

export type Transition<T extends Queries> = (next: FiftyOneLocation) => unknown;

export interface Transitions<T extends Queries> {
  [key: string]: Transition<T>;
}

export interface RouteDefinition<T extends Queries> {
  component: Resource<Route<T>>;
  path: string;
  query: Resource<ConcreteRequest>;
  searchParams: ParameterResolvers<T>;
  transitions?: Transitions<T>;
}

export interface RouteOptions<T extends Queries> {
  component: () => Promise<Route<T>>;
  path: string;
  query: () => Promise<ConcreteRequest>;
  searchParams: ParameterResolvers<T>;
  transitions?: Transitions<T>;
}

export default RouteDefinition;
