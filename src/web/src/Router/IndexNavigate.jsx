import { memo, useEffect, useRef } from "react";
import { Navigate } from "react-router-dom";
import { parseUrlParams } from 'Utils/urlUtils.js';
import { useSystemStore } from 'stores/useSystemStore.js'; 
import { useRaf } from "react-use";

export const IndexNavigate = (props) => {
  const { updateChannel } = useSystemStore();
  const channelRef = useRef(null);

  if (!channelRef.current) {
    const params = parseUrlParams();
    const channel = params.channel || '';
    channelRef.current = channel;
  }
  

  useEffect(() => {
    console.log('channel', channelRef.current)
    updateChannel(channelRef.current);
  }, [updateChannel])

  return <Navigate {...props} />
}

export default memo(IndexNavigate);
