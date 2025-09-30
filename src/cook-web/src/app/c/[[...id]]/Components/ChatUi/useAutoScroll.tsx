import { useEffect, useRef, useCallback } from 'react';

interface UseScrollOptions {
  threshold?: number; // pixel distance treated as "close enough" to bottom
}

function useAutoScroll<T extends HTMLElement>(
  containerRef: React.RefObject<T>,
  opts?: UseScrollOptions,
) {
  const threshold = opts?.threshold ?? 80;
  const autoScrollRef = useRef(true);

  // Determine whether the user is near the bottom of the container
  const checkIfAtBottom = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight;

    if (distanceToBottom <= threshold) {
      // User reached the bottom again → re-enable auto scroll
      autoScrollRef.current = true;
    } else {
      // User scrolled away from the bottom → stop auto scroll
      autoScrollRef.current = false;
    }
  }, [containerRef, threshold]);

  // Track manual scroll events from the user
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const onScroll = () => {
      checkIfAtBottom();
    };

    el.addEventListener('scroll', onScroll, { passive: true });
    checkIfAtBottom(); // initial check on mount
    return () => el.removeEventListener('scroll', onScroll);
  }, [containerRef, checkIfAtBottom]);

  const scrollToBottom = useCallback(
    (behavior: ScrollBehavior = 'auto') => {
      const el = containerRef.current;
      if (!el) return;
      el.scrollTo({ top: el.scrollHeight, behavior });
      autoScrollRef.current = true; // manual call should restore auto scroll
    },
    [containerRef],
  );

  // Auto-scroll on DOM mutations only if user has not opted out
  useEffect(() => {
    const el = containerRef.current;
    if (!el || typeof MutationObserver === 'undefined') return;

    const observer = new MutationObserver(() => {
      if (autoScrollRef.current) {
        requestAnimationFrame(() => scrollToBottom('auto'));
      }
    });

    observer.observe(el, {
      childList: true,
      subtree: true,
      characterData: true,
    });

    return () => observer.disconnect();
  }, [containerRef, scrollToBottom]);

  return {
    scrollToBottom,
    enableAutoScroll: () => {
      autoScrollRef.current = true;
      scrollToBottom('auto');
    },
    disableAutoScroll: () => {
      autoScrollRef.current = false;
    },
    isAutoScrollEnabled: () => autoScrollRef.current,
  };
}

export default useAutoScroll;
