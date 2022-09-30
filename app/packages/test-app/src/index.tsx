import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { RecoilRoot } from "recoil";

const App: React.FC = ({}) => {
  return <h1>Hello World</h1>;
};

createRoot(document.getElementById("root") as HTMLDivElement).render(
  <RecoilRoot>
    <App />
  </RecoilRoot>
);
