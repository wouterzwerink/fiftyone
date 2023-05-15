import { Dataset } from "@fiftyone/core";
import Modal from "@fiftyone/core/src/components/Modal/Modal";
import "@fiftyone/embeddings";
import "@fiftyone/looker-3d";
import "@fiftyone/map";
import "@fiftyone/relay";
import { datasetQueryContext, modal } from "@fiftyone/state";
import { NotFoundError } from "@fiftyone/utilities";
import React from "react";
import { usePreloadedQuery } from "react-relay";
import { useRecoilValue } from "recoil";
import { graphql } from "relay-runtime";
import Nav from "../../components/Nav";
import { Route } from "../../routing";
import style from "../index.module.css";
import { DatasetPageQuery } from "./__generated__/DatasetPageQuery.graphql";

const DatasetPageQueryNode = graphql`
  query DatasetPageQuery(
    $search: String = ""
    $count: Int
    $cursor: String
    $savedViewSlug: String
    $name: String!
    $view: BSONArray!
    $samplesPage: Int
    $samplesCursor: String
  ) {
    dataset(name: $name, view: $view, savedViewSlug: $savedViewSlug) {
      name
      ...datasetFragment
    }
    ...NavFragment
    ...savedViewsFragment
    ...configFragment
    ...samplesFragment
    ...stageDefinitionsFragment
  }
`;

const DatasetPage: Route<DatasetPageQuery> = ({ prepared }) => {
  const data = usePreloadedQuery(DatasetPageQueryNode, prepared);
  const modalActive = Boolean(useRecoilValue(modal));

  if (!data.dataset?.name) {
    throw new NotFoundError({ path: `/datasets/${prepared.variables.name}` });
  }

  return (
    <>
      <Nav fragment={data} hasDataset={true} />
      <div className={style.page}>
        <datasetQueryContext.Provider value={data}>
          <Dataset />
        </datasetQueryContext.Provider>
        {modalActive && <Modal />}
      </div>
    </>
  );
};

export default DatasetPage;
