import { useRecoilCallback } from "recoil";

import * as atoms from "../recoil/atoms";

export default () => {
  return useRecoilCallback(
    ({ set }) =>
      (cursor: string) => {
        set(atoms.modalCursor, cursor);
      },
    []
  );
};
