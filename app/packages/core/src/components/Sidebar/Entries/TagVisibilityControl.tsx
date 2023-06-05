import {
  Autocomplete,
  Box,
  Chip,
  FormControl,
  MenuItem,
  OutlinedInput,
  Select,
  TextField,
} from "@mui/material";
import { useSpring } from "@react-spring/core";
import React from "react";
import { useRecoilValue } from "recoil";

import { useTheme } from "@fiftyone/components";
import * as fos from "@fiftyone/state";

// const ACTIVE_ATOM = {
//   [fos.State.TagKey.LABEL]: fos.activeLabelTags,
//   [fos.State.TagKey.SAMPLE]: fos.activeTags,
// };

// const tagIsActive = selectorFamily<
//   boolean,
//   { key: fos.State.TagKey; tag: string; modal: boolean }
// >({
//   key: "tagIsActive",
//   get:
//     ({ key, tag, modal }) =>
//     ({ get }) =>
//       get(ACTIVE_ATOM[key](modal)).includes(tag),
//   set:
//     ({ key, tag, modal }) =>
//     ({ get, set }) => {
//       const atom = ACTIVE_ATOM[key](modal);
//       const current = get(atom);

//       set(
//         atom,
//         current.includes(tag)
//           ? current.filter((t) => t !== tag)
//           : [tag, ...current]
//       );
//     },
// });

// type MatchEyeProps = {
//   name: string;
//   elementsName: string;
//   onClick: () => void;
//   matched: boolean;
// };

// const MatchEye = ({ elementsName, name, matched, onClick }: MatchEyeProps) => {
//   const theme = useTheme();
//   const color = matched ? theme.text.primary : theme.text.secondary;
//   const title = `Only show ${elementsName} with the "${name}" tag ${
//     matched ? "or other selected tags" : ""
//   }`;

//   return (
//     <span
//       title={title}
//       onClick={(e) => {
//         e.preventDefault();
//         e.stopPropagation();
//         onClick();
//       }}
//       onMouseDown={(e) => {
//         e.preventDefault();
//         e.stopPropagation();
//       }}
//       style={{
//         cursor: "pointer",
//         display: "flex",
//         flexDirection: "column",
//         justifyContent: "center",
//       }}
//     >
//       <Visibility
//         style={{
//           color,
//           height: 20,
//           width: 20,
//         }}
//       />
//     </span>
//   );
// };

const TagVisibilityControl = (props) => {
  const theme = useTheme();
  //   const [active, setActive] = useRecoilState(
  //     tagIsActive({ key: tagKey, modal, tag })
  //   );

  //   const elementsName =
  //     tagKey === fos.State.TagKey.SAMPLE
  //       ? useRecoilValue(fos.elementNames).plural
  //       : "labels";

  //   const [matched, setMatched] = useRecoilState(
  //     tagIsMatched({ key: tagKey, modal, tag })
  //   );

  const { backgroundColor } = useSpring({
    backgroundColor: theme.background.level1,
  });
  console.info(props);
  const labels = useRecoilValue(
    fos.labelTagCounts({ modal: props.modal, extended: false })
  );
  const data = Object.entries(labels).map(([label, _]) => label);
  console.info(labels);
  const ITEM_HEIGHT = 48;
  const ITEM_PADDING_TOP = 8;
  const MenuProps = {
    PaperProps: {
      style: {
        maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
        backgroundColor: theme.background.level1,
      },
    },
  };
  return (
    <div>
      <Autocomplete
        multiple
        id="multiple-limit-tags"
        options={data}
        getOptionLabel={(data) => data}
        defaultValue={data}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Show tags"
            placeholder="Set tag visibility"
          />
        )}
        sx={{
          height: "100%",
          marginTop: "10px",
          backgroundColor: theme.background.level1,
        }}
      />
      {/* <FormControl sx={{ m: 1,  }}>
        <Select
          id={props.name + "-visibility-control"}
          multiple
          value={data}
          onChange={() => {}}
          input={<OutlinedInput id="select-multiple-tags" label="tags" />}
          renderValue={(selected) => (
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
              {selected.map((value) => (
                <Chip key={value} label={value} />
              ))}
            </Box>
          )}
          MenuProps={MenuProps}
        >
          {data.map((name) => (
            <MenuItem key={name} value={name}>
              {name}
            </MenuItem>
          ))}
        </Select>
      </FormControl> */}
      {/* {data.map(([labelName, count]) => (
        <div key={labelName + "-visibility-container"} style={{display: 'flex', flexDirection: "row"}}>
          {props.modal ? (
            <LocalOffer
              style={{ margin: 2, height: 21, width: 21, color: props.color }}
            />
          ) : (
            <Checkbox
              disableRipple={true}
              title={`Set visibility for ${props.name}`}
              checked={false}
              onClick={() => {}}
              style={{
                color: theme.text.secondary,
                padding: 0,
              }}
            />
          )}
          <NameAndCountContainer>
            <span>{labelName}</span>
          </NameAndCountContainer>
        </div>
      ))} */}
    </div>
  );
};

export default React.memo(TagVisibilityControl);
