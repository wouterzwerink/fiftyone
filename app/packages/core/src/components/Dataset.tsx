import React from "react";
import styled from "styled-components";

import SamplesContainer from "./SamplesContainer";

const Container = styled.div`
  height: 100%;
  display: flex;
  flex-direction: column;
`;

const Body = styled.div`
  width: 100%;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
`;

function Dataset() {
  return (
    <Container>
      <Body>
        <SamplesContainer />
      </Body>
    </Container>
  );
}

export default React.memo(Dataset);
