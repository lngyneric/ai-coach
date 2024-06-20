import { create } from 'zustand';

export const useCurrentLessonStore = create((set) => ({
  lessonId: null,
  changeCurrLesson: (lessonId) => set(() => ({ lessonId })),
}));
