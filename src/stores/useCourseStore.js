import { create } from 'zustand';

export const useCourseStore = create((set) => ({
  lessonId: null,
  changeCurrLesson: (lessonId) => set(() => ({ lessonId })),
  purchased: false,
  changePurchased: (purchased) => set(() => ({ purchased })),
}));
