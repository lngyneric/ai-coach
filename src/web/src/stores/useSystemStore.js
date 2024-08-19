import { create } from 'zustand';

export const useSystemStore = create((set) => ({
  language: 'zh_CN',
  channel: '',
  wechatCode: '',
  updateChannel: (channel) => set({ channel }),
  updateweixinCode: (wechatCode) => set({ wechatCode }),
}));
