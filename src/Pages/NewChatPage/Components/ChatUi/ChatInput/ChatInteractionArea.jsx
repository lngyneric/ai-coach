/**
 * 聊天输入区域
 * 目前有三种类型的输入，下一步，文本，按钮组
 */
import styles from './ChatInteractionArea.module.scss';
import ChatInputText from './ChatInputText.jsx';
import ChatButtonGroup from './ChatButtonGroup.jsx';
import ChatInputButton from './ChatInputButton.jsx';
import { INTERACTION_TYPE, INTERACTION_DISPLAY_TYPE } from '@constants/courseContants.js';
import classNames from 'classnames';

const INTERACTION_DISPLAY_MAP = {
  [INTERACTION_TYPE.CONTINUE]: INTERACTION_DISPLAY_TYPE.BUTTON,
  [INTERACTION_TYPE.TEXT]: INTERACTION_DISPLAY_TYPE.TEXT,
  [INTERACTION_TYPE.BUTTONS]: INTERACTION_DISPLAY_TYPE.BUTTONS,
  [INTERACTION_TYPE.NEXT_CHAPTER]: INTERACTION_DISPLAY_TYPE.BUTTON,
  [INTERACTION_TYPE.PHONE]: INTERACTION_DISPLAY_TYPE.TEXT,
  [INTERACTION_TYPE.CHECKCODE]: INTERACTION_DISPLAY_TYPE.TEXT,
};

export const ChatInteractionArea = ({
  type = INTERACTION_DISPLAY_TYPE.TEXT,
  subType = null,
  props = {},
  onSend = (type, val) => {},
  disabled = false,
}) => {
  const displayType = INTERACTION_DISPLAY_MAP[type];

  const onSendFunc = (type, val) => {
    if (disabled) {
      return;
    }
    onSend?.(type, val);
  }

  return (
    <div className={classNames(styles.chatInputArea, disabled && styles.disabled)}>
      {displayType === INTERACTION_DISPLAY_TYPE.BUTTON && (
        <ChatInputButton
          type={type}
          props={props}
          onClick={onSendFunc}
        />
      )}
      {displayType === INTERACTION_DISPLAY_TYPE.TEXT && (
        <ChatInputText
          type={type}
          props={props}
          onClick={onSendFunc}
        />
      )}
      {displayType === INTERACTION_DISPLAY_TYPE.BUTTONS && (
        <ChatButtonGroup
          type={type}
          props={props}
          onClick={onSendFunc}
        />
      )}
    </div>
  );
};

export default ChatInteractionArea;
