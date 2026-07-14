import React from 'react';
interface Props {
  shifuBid?: string;
  onDismiss?: () => void;
  open?: boolean;
  advanceAriaLabel?: string;
  title?: React.ReactNode;
  description?: React.ReactNode;
  stepIndex?: number;
  totalSteps?: number;
  continueLabel?: string;
  targetRect?: DOMRect | null;
  highlightPadding?: number;
  actionLabel?: React.ReactNode;
  actionHref?: string;
  onAdvance?: () => void;
}
export function OnboardingOverlay(props: Props) {
  return null;
}
