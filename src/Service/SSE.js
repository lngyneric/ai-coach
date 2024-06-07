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
      console.log("response", response);
      if (onMessage) {
        onMessage(response);
      }
    } catch (e) {
      console.log("error", e);
    }
  };
  source.onerror = (event) => {
    console.log("连接错误");
    console.log(event);
    // this.searchBoll = true;
  };
  source.onclose = (event) => {
    console.log("会话完成断开连接");
    // this.searchBoll = true;
    console.log(event);
  };
  source.onopen = (event) => {
    console.log("连接成功");
    console.log(event);
  };
  source.close = () => {
    console.log("主动断开连接");
  };
  source.stream();
  return source;
};
