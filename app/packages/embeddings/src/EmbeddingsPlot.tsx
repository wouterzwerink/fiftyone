import { useRecoilValue } from "recoil";
import * as fos from "@fiftyone/state";
import Plot from "react-plotly.js";
import { Loading, useTheme } from "@fiftyone/components";
import { usePanelStatePartial } from "@fiftyone/spaces";
import { tracesToData } from "./tracesToData";
import { useKeyDown } from "./useKeyDown";
import { usePlot } from "./usePlot";
import { useResetPlotZoom, useZoomRevision } from "./useResetPlotZoom";
import { resetZoom } from "@fiftyone/looker/src/elements/common/actions";
import { useCallback } from "react";

export function EmbeddingsPlot({
  brainKey,
  labelField,
  el,
  bounds,
  plotSelection,
}) {
  const theme = useTheme();
  const getColor = useRecoilValue(fos.colorMapRGB(false));
  const datasetName = useRecoilValue(fos.datasetName);
  const {
    setPlotSelection,
    resolvedSelection,
    clearSelection,
    hasSelection,
    handleSelected,
    selectionStyle,
  } = plotSelection;
  const [zoomRev] = useZoomRevision();
  const resetZoom = useResetPlotZoom();
  const { isLoading, traces, style } = usePlot(plotSelection);
  const [dragMode, setDragMode] = usePanelStatePartial("dragMode", "lasso");
  useKeyDown("s", () => setDragMode("lasso"));
  useKeyDown("g", () => setDragMode("pan"));
  useKeyDown(
    "Escape",
    () => {
      if (hasSelection) {
        clearSelection();
      } else {
        resetZoom();
      }
    },
    [hasSelection]
  );
  const colorscale = useRecoilValue(fos.colorscale);

  if (isLoading || !traces) return <Loading>Pixelating...</Loading>;
  console.log({ resolvedSelection, colorscale });
  const data = tracesToData(
    traces,
    style,
    getColor,
    resolvedSelection,
    selectionStyle,
    colorscale
  );
  const isCategorical = style === "categorical";

  return (
    <div style={{ height: "100%" }}>
      {bounds?.width && (
        <Plot
          data={data}
          style={{ zIndex: 1 }}
          onSelected={(selected, foo) => {
            console.log("on selected", { selected, foo });
            if (!selected || selected?.points?.length === 0) return;

            let result = {};
            let pointIds = [];
            for (const p of selected.points) {
              if (!result[p.fullData.name]) {
                result[p.fullData.name] = [];
              }
              result[p.fullData.name].push(p.id);
              pointIds.push(p.id);
            }
            handleSelected(pointIds);
          }}
          onDeselect={() => {
            console.log("on deselected");
            handleSelected(null);
          }}
          config={{
            scrollZoom: true,
            displaylogo: false,
            responsive: true,
            displayModeBar: false,
          }}
          layout={{
            dragmode: dragMode,
            uirevision: zoomRev,
            font: {
              family: "var(--joy-fontFamily-body)",
              size: 14,
            },
            showlegend: isCategorical,
            width: bounds.width,
            height: bounds.height,
            hovermode: false,
            xaxis: {
              showgrid: false,
              zeroline: false,
              visible: false,
            },
            yaxis: {
              showgrid: false,
              zeroline: false,
              visible: false,
              scaleanchor: "x",
              scaleratio: 1,
            },
            autosize: true,
            margin: {
              t: 0,
              l: 0,
              b: 0,
              r: 0,
              pad: 0,
            },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            legend: {
              x: 1,
              y: 1,
              bgcolor: theme.background.level1,
              font: {
                color: theme.text.secondary,
              },
            },
          }}
        />
      )}
    </div>
  );
}