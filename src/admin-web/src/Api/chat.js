import request from "../Service/Request";

/**
 *
 * @param {String} chat_title 聊天标题，可以模糊查询
 * @returns
 */
export const GetAllChatsList = async (chat_title) => {
  return request({
    url: "/api/chat/chat-list",
    method: "get",
    params: { chat_title },
  });
};
export const GetChatDetail = async (chatId) => {
  console.log(chatId);
  return request({
    url: "/api/chat/chat-detail?chat_id=" + chatId,
    method: "get",
  });
};
