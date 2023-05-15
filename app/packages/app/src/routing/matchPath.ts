import { Key, pathToRegexp } from "path-to-regexp";
import { OperationType, VariablesOf } from "relay-runtime";
import { FiftyOneLocation, ParameterResolvers } from "./RouteDefinition";

interface StringKey extends Key {
  name: string;
}

interface CompilePathResult {
  regexp: RegExp;
  keys: StringKey[];
}

const compilePath = (path: string): CompilePathResult => {
  const keys: StringKey[] = [];
  const regexp = pathToRegexp(path, keys, {
    end: true,
    strict: false,
    sensitive: false,
  });
  const result = { regexp, keys };

  return result;
};

interface MatchPathOptions<T extends OperationType> {
  path: string;
  searchParams: ParameterResolvers<T>;
}

export interface MatchPathResult<T extends OperationType> {
  path: string;
  url: string;
  variables: VariablesOf<T>;
}

export const matchPath = <T extends OperationType>(
  location: FiftyOneLocation,
  options: MatchPathOptions<T>
): MatchPathResult<T> | null => {
  const { path, searchParams } = options;

  const { regexp, keys } = compilePath(path);
  const match = regexp.exec(location.pathname);
  if (!match) return null;
  const [url, ...values] = match;

  let all = keys.reduce((acc, key, i) => {
    return { ...acc, [key.name]: decodeURIComponent(values[i]) };
  }, location.state as Partial<VariablesOf<T>>);

  const params = new URLSearchParams(location.search);
  Object.entries(searchParams).forEach(([param, { name, resolver }]) => {
    const value = params.has(param)
      ? decodeURIComponent(params.get(param) as string)
      : null;

    const include = resolver ? resolver(value) : { [name]: value };

    all = {
      ...all,
      ...include,
    };
  });

  return {
    path,
    url: path === "/" && url === "" ? "/" : url,
    variables: all,
  };
};
