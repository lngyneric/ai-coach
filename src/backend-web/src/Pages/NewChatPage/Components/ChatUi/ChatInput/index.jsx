import React, { useState } from 'react';
import styles from "./ChatInput.module.scss";

const ChatApp = () => {
  const [messages, setMessages] = useState([
    { id: 1, role: 'user', content: 'Hello' },
    { id: 2, role: 'ai', content: 'Hi there! How can I assist you today?' },
    { id: 3, role: 'user', content: 'Can you help me with a coding problem?' },
    { id: 4, role: 'ai', content: 'Absolutely! Please provide more details about the problem you\'re working on and I\'ll do my best to help.' },
  ]);
  const [input, setInput] = useState('');

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() !== '') {
      const newMessage = {
        id: messages.length + 1,
        role: 'user',
        content: input,
      };
      setMessages([...messages, newMessage]);
      setInput('');
      // 在这里可以添加向后端API发送消息的逻辑
    }
  };

  return (
    <div className={styles.chatApp}>
      <div className={styles.messageList}>
        {messages.map((message) => (
          <div key={message.id} className={`${styles.message} ${styles[message.role]}`}>
            <span className={styles.role}>{message.role === 'user' ? 'User' : 'AI'}:</span>
            <span className={styles.content}>{message.content}</span>
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className={styles.inputForm}>
        <input
          type="text"
          value={input}
          onChange={handleInputChange}
          placeholder="Type your message..."
          className={styles.inputField}
        />
        <button type="submit" className={styles.submitButton}>提问</button>
      </form>
    </div>
  );
};

export default ChatApp;
