export const LESSON_FEEDBACK_TAIL_INTERACTION_SETTLE_DELAY_MS = 3000;
export const LESSON_FEEDBACK_PROMPT = '';

export function shouldDelayListenFeedbackPromptForTailInteraction() {
  return false;
}

export function isListenLessonFeedbackPromptReady() {
  return true;
}
