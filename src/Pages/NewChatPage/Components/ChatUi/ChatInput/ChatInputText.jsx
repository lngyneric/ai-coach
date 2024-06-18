import { useState } from 'react';
import { message } from 'antd';
import { Input } from '@chatui/core';
import SubButton from 'Components/SubButton.jsx';

import styles from './ChatInputText.module.scss';

export const ChatInputText = () => {
  const [input, setInput] = useState('');
  const [messageApi, contextHolder] = message.useMessage();

  const onSendClick = async (e) => {
    if (input.trim() === '') {
      messageApi.warning('请输入内容');
      return
    }

    setInput('');
  }

  return (
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
  )

};

export default ChatInputText;
