import ChatComponents from "./ChatComponents.jsx";

/**
 * 聊天区的整体画布
 */
export const ChatUi = ({ catalogId, lessonUpdate }) => {
  return (
    <div
      style={{
        height: "100%",
        background: "#F8FBFC",
        flex: "1 1 auto",
      }}
    >
      {<ChatComponents catalogId={catalogId} lessonUpdate={lessonUpdate} />}
      {/* <ChatInput catalogId={catalogId} /> */}
    </div>
  );
};

export default ChatUi;
