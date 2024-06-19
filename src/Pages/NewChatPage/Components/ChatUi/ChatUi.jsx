import ChatComponents from "./ChatComponents.jsx";

/**
 * 聊天区的整体画布
 */
export const ChatUi = ({ catalogId, lessonUpdate, onGoChapter }) => {
  return (
    <div
      style={{
        height: "100%",
        background: "#F8FBFC",
        flex: "1 1 auto",
      }}
    >
      {
        <ChatComponents
          chapterId={catalogId}
          lessonUpdate={lessonUpdate}
          onGoChapter={onGoChapter}
        />
      }
    </div>
  );
};

export default ChatUi;
