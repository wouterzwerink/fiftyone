/**
 * @generated SignedSource<<d4c662b13bd614ebd7e8768d4b10dd1a>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment, RefetchableFragment } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type samplesFragment$data = {
  readonly samples: {
    readonly edges: ReadonlyArray<{
      readonly cursor: string;
      readonly node: {
        readonly __typename: string;
        readonly aspectRatio?: number;
        readonly id?: string;
        readonly sample?: object;
        readonly urls?: ReadonlyArray<{
          readonly field: string;
          readonly url: string | null;
        }>;
      };
    }>;
    readonly total: number | null;
  };
  readonly " $fragmentType": "samplesFragment";
};
export type samplesFragment$key = {
  readonly " $data"?: samplesFragment$data;
  readonly " $fragmentSpreads": FragmentRefs<"samplesFragment">;
};

import samplesFragmentQuery_graphql from './samplesFragmentQuery.graphql';

const node: ReaderFragment = {
  "argumentDefinitions": [
    {
      "kind": "RootArgument",
      "name": "name"
    },
    {
      "kind": "RootArgument",
      "name": "samplesCursor"
    },
    {
      "kind": "RootArgument",
      "name": "samplesPage"
    },
    {
      "kind": "RootArgument",
      "name": "view"
    }
  ],
  "kind": "Fragment",
  "metadata": {
    "refetch": {
      "connection": null,
      "fragmentPathInResult": [],
      "operation": samplesFragmentQuery_graphql
    }
  },
  "name": "samplesFragment",
  "selections": [
    {
      "alias": null,
      "args": [
        {
          "kind": "Variable",
          "name": "after",
          "variableName": "samplesCursor"
        },
        {
          "kind": "Variable",
          "name": "dataset",
          "variableName": "name"
        },
        {
          "kind": "Variable",
          "name": "first",
          "variableName": "samplesPage"
        },
        {
          "kind": "Variable",
          "name": "view",
          "variableName": "view"
        }
      ],
      "concreteType": "SampleItemStrConnection",
      "kind": "LinkedField",
      "name": "samples",
      "plural": false,
      "selections": [
        {
          "alias": null,
          "args": null,
          "kind": "ScalarField",
          "name": "total",
          "storageKey": null
        },
        {
          "alias": null,
          "args": null,
          "concreteType": "SampleItemStrEdge",
          "kind": "LinkedField",
          "name": "edges",
          "plural": true,
          "selections": [
            {
              "alias": null,
              "args": null,
              "kind": "ScalarField",
              "name": "cursor",
              "storageKey": null
            },
            {
              "alias": null,
              "args": null,
              "concreteType": null,
              "kind": "LinkedField",
              "name": "node",
              "plural": false,
              "selections": [
                {
                  "alias": null,
                  "args": null,
                  "kind": "ScalarField",
                  "name": "__typename",
                  "storageKey": null
                },
                {
                  "kind": "InlineFragment",
                  "selections": [
                    {
                      "alias": null,
                      "args": null,
                      "kind": "ScalarField",
                      "name": "id",
                      "storageKey": null
                    },
                    {
                      "alias": null,
                      "args": null,
                      "kind": "ScalarField",
                      "name": "aspectRatio",
                      "storageKey": null
                    },
                    {
                      "alias": null,
                      "args": null,
                      "kind": "ScalarField",
                      "name": "sample",
                      "storageKey": null
                    },
                    {
                      "alias": null,
                      "args": null,
                      "concreteType": "MediaURL",
                      "kind": "LinkedField",
                      "name": "urls",
                      "plural": true,
                      "selections": [
                        {
                          "alias": null,
                          "args": null,
                          "kind": "ScalarField",
                          "name": "field",
                          "storageKey": null
                        },
                        {
                          "alias": null,
                          "args": null,
                          "kind": "ScalarField",
                          "name": "url",
                          "storageKey": null
                        }
                      ],
                      "storageKey": null
                    }
                  ],
                  "type": "Sample",
                  "abstractKey": "__isSample"
                }
              ],
              "storageKey": null
            }
          ],
          "storageKey": null
        }
      ],
      "storageKey": null
    }
  ],
  "type": "Query",
  "abstractKey": null
};

(node as any).hash = "b51e085c5a187e24ca2f885d7868c105";

export default node;
