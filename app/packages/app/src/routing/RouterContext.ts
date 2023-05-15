import { LocationState } from "@fiftyone/relay";
import {
  NotFoundError,
  Resource,
  isElectron,
  isNotebook,
} from "@fiftyone/utilities";
import { Action, createBrowserHistory, createMemoryHistory } from "history";
import React from "react";
import { PreloadedQuery, loadQuery } from "react-relay";
import {
  ConcreteRequest,
  Environment,
  VariablesOf,
  fetchQuery,
} from "relay-runtime";
import { MatchPathResult, Queries, Route, matchPath } from ".";
import RouteDefinition, {
  FiftyOneLocation,
  Transitions,
} from "./RouteDefinition";

export interface RouteData<T extends Queries> {
  path: string;
  url: string;
  variables: VariablesOf<T>;
}

export interface Entry<T extends Queries> extends FiftyOneLocation {
  component: Route<T>;
  concreteRequest: ConcreteRequest;
  preloadedQuery: PreloadedQuery<T>;
  transitions?: Transitions<T>;
  data: T["response"];
  state: LocationState;
  cleanup: () => void;
}

type Subscription = (entry: Entry<Queries>, action?: Action) => void;
type TransitionSubscription<T> = (data: T) => void;

type Subscribe = (
  subscription: Subscription,
  onPending?: () => void
) => () => void;

type TransitionSubscribe<T> = (
  transition: string,
  subscription: TransitionSubscription<T>
) => () => void;

export interface RoutingContext<T extends Queries> {
  history: ReturnType<typeof createBrowserHistory>;
  get: () => Entry<T>;
  load: (hard?: boolean) => Promise<Entry<T>>;
  subscribe: Subscribe;
  transitionSubscribe: TransitionSubscribe<any>;
}

export interface Router<T extends Queries> {
  cleanup: () => void;
  context: RoutingContext<T>;
}

export const createRouter = (
  environment: Environment,
  routes: RouteDefinition<Queries>[]
): Router<Queries> => {
  const history =
    isElectron() || isNotebook()
      ? createMemoryHistory()
      : createBrowserHistory();

  let currentEntryResource: Resource<Entry<Queries>>;

  let nextId = 0;
  const subscribers = new Map<
    number,
    [Subscription, (() => void) | undefined]
  >();

  const transitionSubscribers = new Map<string, Set<(data: unknown) => void>>();

  const update = (location: FiftyOneLocation, action?: Action) => {
    requestAnimationFrame(() =>
      subscribers.forEach(([_, onPending]) => onPending && onPending())
    );

    const current = currentEntryResource.get();

    if (!current) {
      throw new Error("expected entry");
    }

    const { route, matchResult } = matchRoute(
      history.location as FiftyOneLocation,
      routes
    );

    if (location.pathname === current.pathname) {
      const transitions = Object.entries(current?.transitions || {})
        .map<[string, unknown]>(([_, trigger]) => [_, trigger(location)])
        .filter(([_, data]) => data);

      if (transitions.length > 1) {
        throw new Error("only one transition allowed");
      } else if (transitions.length) {
        const [name, data] = transitions[0];
        requestAnimationFrame(() => {
          transitionSubscribers.get(name)?.forEach((fn) => {
            fn(data);
          });
        });
        return;
      }
    }

    currentEntryResource.load().then(({ cleanup }) => {
      currentEntryResource = getEntryResource(
        environment,
        route,
        matchResult.variables,
        location as FiftyOneLocation
      );

      currentEntryResource.load().then((entry) => {
        requestAnimationFrame(() => {
          subscribers.forEach(([cb]) => cb(entry, action));
          cleanup();
        });
      });
    });
  };

  const cleanup = history.listen(({ location, action }) => {
    if (!currentEntryResource) return;

    update(location as FiftyOneLocation, action);
  });

  const context: RoutingContext<Queries> = {
    history,
    load(hard = false) {
      const runUpdate = currentEntryResource && hard;
      if (!currentEntryResource || hard) {
        const { route, matchResult } = matchRoute(
          history.location as FiftyOneLocation,
          routes
        );
        currentEntryResource = getEntryResource(
          environment,
          route,
          matchResult.variables,
          history.location as FiftyOneLocation,
          hard
        );
      }
      runUpdate && update(history.location as FiftyOneLocation);
      return currentEntryResource.load();
    },
    get() {
      if (!currentEntryResource) {
        throw new Error("no entry loaded");
      }
      const entry = currentEntryResource.get();
      if (!entry) {
        throw new Error("entry is loading");
      }
      return entry;
    },
    subscribe(cb, onPending) {
      const id = nextId++;
      const dispose = () => {
        subscribers.delete(id);
      };
      subscribers.set(id, [cb, onPending]);
      return dispose;
    },
    transitionSubscribe(transition, cb) {
      !transitionSubscribers.has(transition) &&
        transitionSubscribers.set(transition, new Set());
      transitionSubscribers.get(transition)?.add(cb);

      return () => {
        transitionSubscribers.get(transition)?.delete(cb);
      };
    },
  };

  return {
    cleanup,
    context,
  };
};

const getEntryResource = <T extends Queries>(
  environment: Environment,
  route: RouteDefinition<T>,
  variables: VariablesOf<T>,
  location: FiftyOneLocation,
  hard = false
): Resource<Entry<T>> => {
  const fetchPolicy = hard ? "network-only" : "store-or-network";

  return new Resource(() => {
    return Promise.all([route.component.load(), route.query.load()]).then(
      ([component, concreteRequest]) => {
        const preloadedQuery = loadQuery(
          environment,
          concreteRequest,
          variables || {},
          {
            fetchPolicy,
          }
        );

        let resolveEntry: (entry: Entry<T>) => void;
        let rejectEntry: (reason?: any) => void;
        const promise = new Promise<Entry<T>>((resolve, reject) => {
          resolveEntry = resolve;
          rejectEntry = reject;
        });
        const subscription = fetchQuery(
          environment,
          concreteRequest,
          variables || {},
          { fetchPolicy }
        ).subscribe({
          next: (data) => {
            resolveEntry({
              ...location,
              component,
              data,
              concreteRequest,
              preloadedQuery,
              cleanup: () => {
                subscription?.unsubscribe();
              },
              transitions: route.transitions,
            });
          },

          error: (error) => rejectEntry(error),
        });

        return promise;
      }
    );
  });
};

const matchRoute = <T extends Queries>(
  location: FiftyOneLocation,
  routes: RouteDefinition<T>[]
) => {
  let route: RouteDefinition<T> | undefined = undefined;
  let matchResult: MatchPathResult<T> | undefined = undefined;
  for (let index = 0; index < routes.length; index++) {
    route = routes[index];
    const match = matchPath<T>(location, route);

    if (match) {
      matchResult = match;
      break;
    }
  }

  if (!matchResult || !route) {
    throw new NotFoundError({ path: location.pathname });
  }

  return { route, matchResult };
};

export const RouterContext = React.createContext<
  RoutingContext<Queries> | undefined
>(undefined);
