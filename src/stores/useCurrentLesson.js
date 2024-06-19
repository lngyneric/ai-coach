import { create } from 'zustand';

export const useCurrentLesson = create((set) => ({
  lessonId: null,
  changeCurrLesson: (lessonId) => set(() => ({ lessonId })),
}));
