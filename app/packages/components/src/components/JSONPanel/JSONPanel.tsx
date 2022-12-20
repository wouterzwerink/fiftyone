/**
 * Copyright 2017-2022, Voxel51, Inc.
 */
import { Copy as CopyIcon, Close as CloseIcon } from "@fiftyone/components";
import ReactJson from "react-json-view";
import {
  lookerPanel,
  lookerPanelContainer,
  lookerPanelVerticalContainer,
} from "./panel.module.css";
import {
  lookerCopyJSON,
  lookerCloseJSON,
  lookerJSONPanel,
} from "./json.module.css";

export default function JSONPanel({
  containerRef,
  jsonHTML,
  onClose,
  onCopy,
  json,
  sample,
}) {
  console.log("HERE is the JSON HTML", jsonHTML);
  console.log("HERE is the JSON", json);
  console.log("HERE is the JSON sample", sample);
  return (
    <div
      ref={containerRef}
      className={`${lookerJSONPanel} ${lookerPanelContainer}`}
      onClick={(e) => e.stopPropagation()}
    >
      <div className={lookerPanelVerticalContainer}>
        <div className={lookerPanel}>
          {/* {jsonHTML && <pre dangerouslySetInnerHTML={jsonHTML} />} */}
          <ReactJson
            src={sample}
            collapsed={false}
            theme={"brewer"}
            collapseStringsAfterLength={30}
          />
        </div>
        <CloseIcon
          className={lookerCloseJSON}
          titleAccess="Close JSON"
          onClick={onClose}
          sx={{
            fontSize: "1.75rem",
          }}
        />
        <CopyIcon
          className={lookerCopyJSON}
          titleAccess="Copy JSON to clipboard"
          onClick={onCopy}
          sx={{
            fontSize: "1.75rem",
          }}
        />
      </div>
    </div>
  );
}
