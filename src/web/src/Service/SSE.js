import { SSE } from "sse.js";
import Cookies from "js-cookie";
import store from "store";

const url = (process.env.REACT_APP_BASEURL || "") + "/api/chat/chat-assistant";

export const SendMsg = (chatId, text, onMessage) => {
  var source = new SSE(url + "?token=" + store.get("token"), {
    headers: { "Content-Type": "application/json" },
    payload: JSON.stringify({
      msg: text,
      chat_id: chatId,
    }),
  });
  source.onmessage = (event) => {
    try {
      // var response = eval('('+event.data+")")
      var response = JSON.parse(event.data);
      if (onMessage) {
        onMessage(response);
      }
    } catch (e) {
      console.log("error", e);
    }
  };
  source.onerror = (event) => {
  };
  source.onclose = (event) => {
  };
  source.onopen = (event) => {
  };
  source.close = () => {
  };
  source.stream();
  return source;
};
