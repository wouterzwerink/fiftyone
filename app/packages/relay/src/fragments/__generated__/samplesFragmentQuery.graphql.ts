/**
 * @generated SignedSource<<cc54bcf9e996b4d185de57ea5abf930f>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest, Query } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type samplesFragmentQuery$variables = {
  name: string;
  samplesCursor?: string | null;
  samplesPage?: number | null;
  view: Array;
};
export type samplesFragmentQuery$data = {
  readonly " $fragmentSpreads": FragmentRefs<"samplesFragment">;
};
export type samplesFragmentQuery = {
  response: samplesFragmentQuery$data;
  variables: samplesFragmentQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "name"
  },
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "samplesCursor"
  },
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "samplesPage"
  },
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "view"
  }
],
v1 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "id",
  "storageKey": null
},
v2 = [
  (v1/*: any*/)
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "samplesFragmentQuery",
    "selections": [
      {
        "args": null,
        "kind": "FragmentSpread",
        "name": "samplesFragment"
      }
    ],
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "samplesFragmentQuery",
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
                      (v1/*: any*/),
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
                  },
                  {
                    "kind": "InlineFragment",
                    "selections": (v2/*: any*/),
                    "type": "ImageSample",
                    "abstractKey": null
                  },
                  {
                    "kind": "InlineFragment",
                    "selections": (v2/*: any*/),
                    "type": "PointCloudSample",
                    "abstractKey": null
                  },
                  {
                    "kind": "InlineFragment",
                    "selections": (v2/*: any*/),
                    "type": "VideoSample",
                    "abstractKey": null
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
    ]
  },
  "params": {
    "cacheID": "7b5b1a69da91bb1df357a134cc5c7ff2",
    "id": null,
    "metadata": {},
    "name": "samplesFragmentQuery",
    "operationKind": "query",
    "text": "query samplesFragmentQuery(\n  $name: String!\n  $samplesCursor: String\n  $samplesPage: Int\n  $view: BSONArray!\n) {\n  ...samplesFragment\n}\n\nfragment samplesFragment on Query {\n  samples(dataset: $name, view: $view, first: $samplesPage, after: $samplesCursor) {\n    total\n    edges {\n      cursor\n      node {\n        __typename\n        ... on Sample {\n          __isSample: __typename\n          id\n          aspectRatio\n          sample\n          urls {\n            field\n            url\n          }\n        }\n        ... on ImageSample {\n          id\n        }\n        ... on PointCloudSample {\n          id\n        }\n        ... on VideoSample {\n          id\n        }\n      }\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "b51e085c5a187e24ca2f885d7868c105";

export default node;
