import { useState } from "react"

import { FRAME_LAYOUT_LOOSE } from '@constants/uiContants.js';

export const useUiLayout = (props) => {
  const [frameLayout, setFrameLayout] = useState(FRAME_LAYOUT_LOOSE);
  const [isMobile, setIsMobile] = useState(false);

  return {
    frameLayout,
    setFrameLayout,
    isMobile,
    setIsMobile,
  }
}
