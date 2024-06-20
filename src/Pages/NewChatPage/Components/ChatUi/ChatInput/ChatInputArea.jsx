/**
 * 聊天输入区域
 * 目前有三种类型的输入，下一步，文本，按钮组
 */
import MainButton from 'Components/MainButton.jsx';
import styles from './ChatInputArea.module.scss';
import ChatInputText from './ChatInputText.jsx';
import ChatButtonGroup from './ChatButtonGroup.jsx';
import ChatInputButton from './ChatInputButton.jsx';
import { INPUT_TYPE } from '@constants/courseContants.js';

export const ChatInputArea = ({ type = 'text', subType = null, props = {}, onSend = (type, val) => {}}) => {
  return (
    <div className={styles.chatInputArea}>
      {
        type === INPUT_TYPE.CONTINUE &&
        <div className={styles.continueWrapper}>
          <ChatInputButton type={type} subType={subType} props={props} onClick={(type, val) => { onSend(type, val) }} />
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
          <ChatButtonGroup buttons={props.buttons} onClick={(val) => { onSend?.(INPUT_TYPE.SELECT, val) }} />
        </div>
      }
    </div>
  )
}

export default ChatInputArea;
