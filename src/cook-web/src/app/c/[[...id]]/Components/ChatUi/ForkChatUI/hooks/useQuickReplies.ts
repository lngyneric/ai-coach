import { useState, useEffect, useRef } from 'react';
import { QuickReplyItemProps } from '../components/QuickReplies';

type QuickReplies = QuickReplyItemProps[];

export default function useQuickReplies(initialState: QuickReplies = []) {
  const [quickReplies, setQuickReplies] = useState(initialState);
  const [visible, setVisible] = useState(true);
  const savedRef = useRef<QuickReplies>(null);
  const stashRef = useRef<QuickReplies>(null);

  useEffect(() => {
    savedRef.current = quickReplies;
  }, [quickReplies]);

  const prepend = (list: QuickReplies) => {
    setQuickReplies(prev => [...list, ...prev]);
  };

  // Calling save immediately after prepend/replace only captures the previous state
  // Because savedRef.current updates last, wrapping it in setTimeout resolves the timing issue
  const save = () => {
    stashRef.current = savedRef.current;
  };

  const pop = () => {
    if (stashRef.current) {
      setQuickReplies(stashRef.current);
    }
  };

  return {
    quickReplies,
    prepend,
    replace: setQuickReplies,
    visible,
    setVisible,
    save,
    pop,
  };
}
