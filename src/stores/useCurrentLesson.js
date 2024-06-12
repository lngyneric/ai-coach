import { create } from 'zustand';

export const useCurrentLesson = create((set) => ({
  lessonId: null,
  setLessonId: (lessonId) => set(() => ({ lessonId })),
}));
