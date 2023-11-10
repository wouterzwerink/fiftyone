/* 
In color by value mode, fields and label tags use this component 
*/

import { PopoutDiv, useTheme } from "@fiftyone/components";
import { useOutsideClick } from "@fiftyone/state";
import KeyboardArrowDownOutlinedIcon from "@mui/icons-material/KeyboardArrowDownOutlined";
import KeyboardArrowUpOutlinedIcon from "@mui/icons-material/KeyboardArrowUpOutlined";
import React, { ForwardedRef } from "react";
import styled from "styled-components";
import { sampleColorscale } from "../colorscaleConstants";

const ActionDiv = styled.div`
  position: relative;
`;

const SelectButton = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem;
  margin: 0.25rem;
  background-color: ${({ theme }) => theme.background.level3};
`;

type ColorStop = [number, string];
type ColorScale = ColorStop[];

interface Scales {
  [key: string]: ColorScale;
}

interface ColorScaleProps {
  name: string;
  scale: ColorScale;
  onClick: (name: string) => void;
}

const ColorScaleDisplay: React.FC<ColorScaleProps> = ({
  name,
  scale,
  onClick,
}) => {
  const OptionDiv = styled.div`
    cursor: pointer;
    background-color: ${({ theme }) => theme.background.secondary};
    &:hover {
      background-color: ${({ theme }) => theme.background.secondary};
    }
    display: flex;
    align-items: "center";
    margin-bottom: "1rem";
  `;

  const gradientStops = scale
    .map((stop) => `${stop[1]} ${stop[0] * 100}%`)
    .join(", ");
  const style = {
    background: `linear-gradient(90deg, ${gradientStops})`,
    width: "100%",
    height: "20px",
    borderRadius: "5px",
  };

  return (
    <OptionDiv onClick={() => onClick(name)}>
      <div style={style} />
      <span style={{ marginLeft: "10px" }}>{name}</span>
    </OptionDiv>
  );
};

type NamedColorScaleSelectionProp = {
  value: string;
  style: React.CSSProperties;
  onValidate?: (value: string) => boolean;
  onSyncUpdate: (input: string) => void;
};

const NamedColorScaleSelection: React.FC<NamedColorScaleSelectionProp> = ({
  value,
  style,
  onValidate,
  onSyncUpdate,
}) => {
  const theme = useTheme();
  const ref = React.useRef<HTMLDivElement>(null);
  const [open, setOpen] = React.useState(false);
  useOutsideClick(ref, () => open && setOpen(false));

  const onClick = (name: string) => {
    onSyncUpdate(name);
  };

  return (
    <div style={style}>
      <ActionDiv>
        <SelectButton
          onClick={() => setOpen((o) => !o)}
          theme={theme}
          data-cy="select-colorscale-attribute"
        >
          <div>{value && value !== "" ? value : "Select a colorscale"}</div>
          {open ? (
            <KeyboardArrowUpOutlinedIcon />
          ) : (
            <KeyboardArrowDownOutlinedIcon />
          )}
          {open && (
            <PopoutDiv
              style={{ zIndex: 1000000001, opacity: 1, width: "100%" }}
            >
              {Object.entries(sampleColorscale).map(([name, scale]) => (
                <ColorItem
                  key={name}
                  name={name}
                  scale={scale}
                  onClick={onClick}
                />
              ))}
            </PopoutDiv>
          )}
        </SelectButton>
      </ActionDiv>
    </div>
  );
};

export default NamedColorScaleSelection;

type ItemProp = {
  onClick: (name: string) => void;
  name: string;
  key: string;
  scale: (string | number)[][];
};

const ColorItem = React.memo(
  React.forwardRef(
    (
      { onClick, name, key, scale }: ItemProp,
      ref: ForwardedRef<HTMLDivElement>
    ) => {
      return (
        <ColorScaleDisplay
          key={name}
          name={name}
          scale={scale}
          onClick={onClick}
        />
      );
    }
  )
);

function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}
