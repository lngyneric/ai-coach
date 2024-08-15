import { useCallback } from 'react';
import { tracking } from 'common/tools/tracking.js';


export const useTracking = () => {
  const getEventBasicData = useCallback(() => {
    return {
      user_type: '',
      user_id: '',
      device: '',
    }
  }, [])

  const trackingEvent = useCallback(async (eventName, eventData) => {
    trackingEvent(eventName, eventData);
  }, [])

  return { tracking: trackingEvent }
}
