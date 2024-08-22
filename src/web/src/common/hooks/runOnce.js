import { useState, useCallback } from "react";

export const useRunOnce = ({ fn }) => {
  const [hasRun, setHasRun] = useState(false);

  const run = useCallback(async () => {
    if (hasRun) {
      return;
    }
    setHasRun(true);
    return fn?.();
  }, [fn, hasRun]);

  const reset = useCallback(() => {
    setHasRun(false);
  }, []);

  return { run, reset };
};
