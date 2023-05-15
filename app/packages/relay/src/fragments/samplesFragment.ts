import { graphql } from "react-relay";

export default graphql`
  fragment samplesFragment on Query
  @refetchable(queryName: "samplesFragmentQuery") {
    samples(
      dataset: $name
      view: $view
      first: $samplesPage
      after: $samplesCursor
    ) {
      total
      edges {
        cursor
        node {
          __typename
          ... on Sample {
            id
            aspectRatio
            sample
            urls {
              field
              url
            }
          }
        }
      }
    }
  }
`;
