import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware'

export const useCourseStore = create(
  subscribeWithSelector((set) => ({
    lessonId: null,
    changeCurrLesson: (lessonId) => set(() => ({ lessonId })),
    chapterId: '',
    updateChapterId: (chapterId) => set(() => { console.log('updateChapterId:'); return { chapterId }; }),
    purchased: false,
    changePurchased: (purchased) => set(() => ({ purchased })),
  })));
