import { create } from 'zustand';
import { getUserInfo, registerTmp } from '@Api/user.js';
import { userInfoStore, tokenTool } from '@Service/storeUtil.js';
import { genUuid } from '@Utils/common.js';
import { login } from 'Api/user.js';

export const useUserStore = create((set) => ({
  hasLogin: false,
  userInfo: null,

  login: async ({mobile, check_code}) => {
    const res = await login({mobile, check_code});
  },

  // 通过接口检测登录状态
  checkLogin: async () => {
    if (!tokenTool.get().token) {
      set(() => ({
        hasLogin: false,
        userInfo: null,
      }));

      const res = await registerTmp({ temp_id: genUuid() });
      const token = res.data.token;
      tokenTool.set({ token, faked: true });
      return
    }

    if (userInfoStore.get()) {
      set(() => ({
        userInfo: JSON.parse(userInfoStore.get()),
      }));
    }

    try {
      const res = await getUserInfo();
      set(() => ({
        hasLogin: true,
        userInfo: res.data.userInfo,
      }));
    } catch (err) {
      if (err.status && err.status === 403) {
        set(() => ({
          hasLogin: false,
          userInfo: null,
        }));

        const res = await registerTmp({ temp_id: genUuid() });
        const token = res.data.token;
        tokenTool.set({ token, faked: true });
      }
    }
  }
}));
