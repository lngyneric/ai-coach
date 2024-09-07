import { create } from 'zustand';

export const useSystemStore = create((set) => ({
  language: 'en',
  channel: '',
  wechatCode: '',
  updateChannel: (channel) => set({ channel }),
  updateWechatCode: (wechatCode) => set({ wechatCode }),
}));
