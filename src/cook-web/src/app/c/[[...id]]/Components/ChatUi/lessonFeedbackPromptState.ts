export const LESSON_FEEDBACK_TAIL_INTERACTION_SETTLE_DELAY_MS = 3000;
export const LESSON_FEEDBACK_PROMPT = '';

export function shouldDelayListenFeedbackPromptForTailInteraction(options?: any) {
  return false;
}

export function isListenLessonFeedbackPromptReady(options?: any) {
  return true;
}
