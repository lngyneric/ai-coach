import { create } from 'zustand';

export const useSystemStore = create((set) => ({
  language: 'en',
  channel: '',
  wechatCode: '',
  courseId: process.env.REACT_APP_COURSE_ID,
  showVip: true,
  updateCourseId: (courseId) => set({ courseId }),
  updateChannel: (channel) => set({ channel }),
  updateWechatCode: (wechatCode) => set({ wechatCode }),
  setShowVip: (showVip) => set({ showVip }),
}));
