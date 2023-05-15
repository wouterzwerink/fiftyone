import { useRecoilCallback } from "recoil";

import * as fos from "../recoil";

/**
 * A react hook that allows clearing the modal state.
 *
 * @example
 * ```ts
 * function MyComponent() {
 *   const clearModal = useClearModal();
 *   return (
 *    <button onClick={clearModal}>Close Modal</button>
 *   )
 * }
 * ```
 *
 * @returns A function that clears the modal state.
 */

export default () => {
  return useRecoilCallback(
    ({ set }) =>
      () => {
        set(fos.modal, null);
      },
    []
  );
};
