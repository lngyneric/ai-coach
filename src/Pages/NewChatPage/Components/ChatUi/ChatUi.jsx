import ChatComponents from "./ChatComponents.jsx";
import styles from './ChatUi.module.scss';

/**
 * 聊天区的整体画布
 */
export const ChatUi = ({ catalogId, lessonUpdate, onGoChapter }) => {
  return (
    <div className={styles.ChatUi} >
      {
        <ChatComponents
          chapterId={catalogId}
          lessonUpdate={lessonUpdate}
          onGoChapter={onGoChapter}
          className={styles.chatComponents}
        />
      }
    </div>
  );
};

export default ChatUi;
