import { default as React } from "react";
import { PreloadedQuery } from "react-relay";
import {
  AtomEffect,
  TransactionInterface_UNSTABLE,
  useRecoilTransaction_UNSTABLE,
} from "recoil";
import { ConcreteRequest, IEnvironment, OperationType } from "relay-runtime";
import { datasetQuery } from "./queries";
import { SelectorEffectContext, Setter } from "./selectorWithEffect";

export type LocationState = {
  view?: object[];
  cursor?: string;
};

export interface PageQuery<T extends OperationType> {
  preloadedQuery: PreloadedQuery<T>;
  concreteRequest: ConcreteRequest;
  data: T["response"];
  state: LocationState;
}

export type PageSubscription<T extends OperationType> = (
  pageQuery: PageQuery<T>,
  transationInterface: TransactionInterface_UNSTABLE
) => void;

let pageQueryReader: <T extends OperationType>() => PageQuery<T>;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const subscribers = new Set<PageSubscription<any>>();
const transitionSubscribers = new Map<
  string,
  Set<
    (
      data: unknown,
      environment: IEnvironment,
      transationInterface: TransactionInterface_UNSTABLE
    ) => void
  >
>([["samplesTransition", new Set()]]);

interface Transitions {
  samplesTransition: string;
}

export function subscribeTransition<K extends keyof Transitions>(
  transition: K,
  subscription: (
    data: Transitions[K],
    environment: IEnvironment,
    transactionInterface: TransactionInterface_UNSTABLE
  ) => void
) {
  transitionSubscribers.get(transition).add(subscription);

  return () => {
    transitionSubscribers.get(transition).delete(subscription);
  };
}

export function subscribe<T extends OperationType>(
  subscription: PageSubscription<T>
) {
  subscribers.add(subscription);

  return () => {
    subscribers.delete(subscription);
  };
}

export function getPageQuery<T extends OperationType>() {
  return { pageQuery: pageQueryReader<T>(), subscribe };
}
/**
 * Effect for restting an atom's value when the view or dataset changes.
 * Can be limited to only dataset changes when viewChange is false
 */
export const resetEffect = <T extends unknown>(
  viewChange = true
): AtomEffect<T> => {
  return ({ trigger, node }) => {
    if (trigger === "get") {
      const initialPage = getPageQuery<datasetQuery>();
      const currentDatasetName =
        initialPage.pageQuery.preloadedQuery.variables.name;
      const currentView =
        initialPage.pageQuery.preloadedQuery.variables.savedViewSlug ||
        initialPage.pageQuery.preloadedQuery.variables.view;
      return subscribe<datasetQuery>(({ preloadedQuery }, { reset }) => {
        if (preloadedQuery.variables.name !== currentDatasetName) {
          const view =
            preloadedQuery.variables.savedViewSlug ||
            preloadedQuery.variables.view;
          if (!viewChange || view !== currentView) {
            reset(node);
          }
        }
      });
    }
  };
};

type WriterProps<T extends OperationType> = React.PropsWithChildren<{
  read: () => PageQuery<T>;
  setters: Map<string, Setter>;
  subscribe: (
    fn: (pageQuery: PageQuery<T>) => void,
    transtionsFn: (name: string, data: unknown) => void
  ) => () => void;
}>;

/**
 * A Recoil/Relay atomic syncing interface between a current page query
 * and atom and atom families
 */
export function Writer<T extends OperationType>({
  children,
  read,
  subscribe,
  setters,
}: WriterProps<T>) {
  // @ts-ignore
  pageQueryReader = read;

  const set = useRecoilTransaction_UNSTABLE(
    (transactionInterface) =>
      (cb: (TransactionInterface: TransactionInterface_UNSTABLE) => void) => {
        cb(transactionInterface);
      },
    []
  );

  React.useEffect(() => {
    return subscribe(
      (pageQuery) => {
        // @ts-ignore
        pageQueryReader = () => pageQuery;
        set((transactionInterface) =>
          subscribers.forEach((cb) => cb(pageQuery, transactionInterface))
        );
      },
      (name: string, data: unknown) => {
        set((transactionInterface) =>
          transitionSubscribers
            .get(name)
            .forEach((cb) =>
              cb(
                data,
                pageQueryReader().preloadedQuery.environment,
                transactionInterface
              )
            )
        );
      }
    );
  }, [set, subscribe]);

  return (
    <SelectorEffectContext setters={setters}>{children}</SelectorEffectContext>
  );
}

export default Writer;
