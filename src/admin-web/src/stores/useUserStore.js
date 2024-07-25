import { create } from 'zustand';
import { getUserInfo } from '@Api/user.js';
import { tokenStore, userInfoStore } from '@Service/storeUtil.js';
import { C, er } from '@fullcalendar/core/internal-common';

export const useUserStore = create((set) => ({
  isLogin: false,
  userInfo: null,

  checkLogin: async () => {
    if (!tokenStore.get()) {
      set(() => {
        return {
          isLogin: false,
          userInfo: null,
        }
      });
    }

    if (userInfoStore.get()) {
      set(() => {
        return {
          userInfo: JSON.parse(userInfoStore.get()),
        }
      });
    }


    try {
      const res = await getUserInfo();
      set(() => {
        return {
          isLogin: true,
          userInfo: res.data,
        }
      })
    } catch (err) {
      console.log(err)
      if (err.status && err.status === 403) {
        set(() => {
          return {
            isLogin: false,
            userInfo: null,
          }
        });
        tokenStore.remove();
      }
    }
  }
}));
