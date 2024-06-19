/**
 * 聊天输入区域
 * 目前有三种类型的输入，下一步，文本，按钮组
 */
import MainButton from 'Components/MainButton.jsx';
import styles from './ChatInputArea.module.scss';
import ChatInputText from './ChatInputText.jsx';
import ChatButtonGroup from './ChatButtonGroup.jsx';

export const INPUT_TYPE = {
  CONTINUE: 'continue', // 下一步
  TEXT: 'text', // 文本
  BUTTONS: 'buttons', // 按钮组
};

export const ChatInputArea = ({ type = 'text', content, buttons, onSend = (type, val) => {}}) => {
  return (
    <div className={styles.chatInputArea}>
      {
        type === INPUT_TYPE.CONTINUE &&
        <div className={styles.continueWrapper}>
          <MainButton className={styles.continueBtn} width="90%" onClick={() => onSend?.(INPUT_TYPE.CONTINUE, content)}>{content}</MainButton>
        </div>
      }
      {
        type === INPUT_TYPE.TEXT &&
        <div className={styles.inputTextWrapper}>
          <ChatInputText
            onClick={(val) => {
              onSend?.(INPUT_TYPE.TEXT, val);
            }}
          />
        </div>
      }
      {
        type === INPUT_TYPE.BUTTONS &&
        <div className={styles.buttonGroupWrapper}>
          <ChatButtonGroup />
        </div>
      }
    </div>
  )
}

export default ChatInputArea;
