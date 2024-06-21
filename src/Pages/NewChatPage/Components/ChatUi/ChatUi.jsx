import ChatComponents from "./ChatComponents.jsx";
import styles from './ChatUi.module.scss';

/**
 * 聊天区的整体画布
 */
export const ChatUi = ({ chapterId, lessonUpdate, onGoChapter, onPurchased }) => {
  return (
    <div className={styles.ChatUi} >
      {
        <ChatComponents
          chapterId={chapterId}
          lessonUpdate={lessonUpdate}
          onGoChapter={onGoChapter}
          className={styles.chatComponents}
          onPurchased={onPurchased}
        />
      }
    </div>
  );
};

export default ChatUi;
