import { create } from 'zustand';
import { isMobile } from 'react-device-detect';
import { FRAME_LAYOUT_PC } from '@constants/uiConstants.js';

export const useUiLayoutStore = create((set) => ({
  frameLayout: FRAME_LAYOUT_PC,
  inMobile: isMobile,
  inWeixin: false,
  updateFrameLayout: (frameLayout) => set(() => ({ frameLayout })),
  checkMobileEnv: () => set(() => {
    return {
      inMobile: isMobile,
      isWeixin: /MicroMessenger/i.test(window.navigator.userAgent),
    }
  }),
}));
