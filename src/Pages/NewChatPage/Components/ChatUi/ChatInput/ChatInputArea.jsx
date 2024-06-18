/**
 * 聊天输入区域
 * 目前有三种类型的输入，下一步，文本，按钮组
 */
import MainButton from 'Components/MainButton.jsx';
import styles from './ChatInputArea.module.scss';
import ChatInputText from './ChatInputText.jsx';

const INPUT_TYPE = {
  CONTINUE: 'continue', // 下一步
  TEXT: 'text', // 文本
  SELECT: 'select', // 按钮组
};


export const ChatInputArea = ({ onSend, type = 'text', text, buttons }) => {
  return (
    <div className={styles.chatInputArea}>
      {
        type === INPUT_TYPE.CONTINUE &&
        <div className={styles.continueWrapper}>
          <MainButton className={styles.continueBtn} width="100%">下一步</MainButton>
        </div>
      }
      {
        <div className={styles.inputTextWrapper}>
          <ChatInputText />
        </div>
      }
    </div>
  )
}

export default ChatInputArea;
