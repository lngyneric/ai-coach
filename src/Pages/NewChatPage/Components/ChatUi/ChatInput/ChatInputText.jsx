import { useState } from 'react';
import { message } from 'antd';
import { Input } from '@chatui/core';
import SubButton from 'Components/SubButton.jsx';
import { INTERACTION_TYPE, INTERACTION_OUTPUT_TYPE } from '@constants/courseContants.js';

import styles from './ChatInputText.module.scss';

const OUTPUT_TYPE_MAP = {
  [INTERACTION_TYPE.TEXT]: INTERACTION_OUTPUT_TYPE.TEXT,
  [INTERACTION_TYPE.PHONE]: INTERACTION_OUTPUT_TYPE.PHONE,
  [INTERACTION_TYPE.CHECKCODE]: INTERACTION_OUTPUT_TYPE.CHECKCODE,
}

export const ChatInputText = ({ onClick, type }) => {
  const [input, setInput] = useState('');
  const [messageApi, contextHolder] = message.useMessage();

  const output_type = OUTPUT_TYPE_MAP[type];

  const onSendClick = async () => {
    if (input.trim() === '') {
      messageApi.warning('请输入内容');
      return
    }

    onClick?.(output_type, input.trim());
    setInput('');
  }

  return (
    <div className={styles.inputTextWrapper}>
      <div className={styles.inputForm}>
        <div className={styles.inputWrapper}>
          <Input
            autoSize
            type="text"
            value={input}
            onChange={v => setInput(v)}
            placeholder=""
            className={styles.inputField}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onSendClick();
              }
            }}
          />
        </div>
        <SubButton onClick={onSendClick} width={100} height={32} style={{ marginLeft: '15px' }} >提问</SubButton>
        {contextHolder}
      </div>
    </div>
  )

};

export default ChatInputText;
