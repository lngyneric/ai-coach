import React, { useState, useEffect } from "react";
import axios from "axios";
import styles from "./ChatInput.module.scss";
import { Run } from "@Utils";
import { getLessonStudyRecord } from '@Api/study.js';

const ChatApp = ({ catalogId }) => {
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState([
    { id: 1, role: "user", content: "Hello" },
    { id: 2, role: "ai", content: "Hi there! How can I assist you today?" },
    { id: 3, role: "user", content: "Can you help me with a coding problem?" },
    {
      id: 4,
      role: "ai",
      content:
        "Absolutely! Please provide more details about the problem you're working on and I'll do my best to help.",
    },
  ]);
  const [input, setInput] = useState("");

  // 定义当前的类型
  const [currentMessage, setCurrentMessage] = useState("");
  const token = process.env.REACT_APP_TOKEN;

  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const response = await fetch(
          `https://test-api-sifu.agiclass.cn/api/study/run?token=${token}`,
          {
            headers: {
              Accept: "application/json",
            },
          }
        );
        const messageData = await response.json();
        if (messageData.type === "text") {
          setCurrentMessage((prev) => prev + messageData.content);
        } else if (messageData.type === "text_end") {
          setMessages((prevMessages) => [
            ...prevMessages,
            {
              id: prevMessages.length + 1,
              role: "ai",
              content: currentMessage,
            },
          ]);
          setCurrentMessage("");
        }
      } catch (error) {
        console.error("Fetch error:", error);
      }
    };

    fetchMessages();
  }, [token, currentMessage]);

  useEffect(() => {
    console.log('useEffect.catalogId', catalogId);
    if (!catalogId) {
      return
    }
    (async () => {
      const resp = await getLessonStudyRecord(catalogId);
      const records = resp.data.records;

      const nextMessages = records.map((v, i) => {
        return {
          role: v.script_role,
          content: v.script_content,
          id: v.i,
          type: v.script_type,
        };
      })

      setMessages(nextMessages);
    })();  
  }, [catalogId]);

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (input.trim() !== "") {
      const newMessage = {
        id: messages.length + 1,
        role: "user",
        content: input,
      };
      setMessages([...messages, newMessage]);
      setInput("");
      Run({
        "lesson_id": "4ec0deaa454d474b9a3baa4a3e4d4ced",
        "input": "",
        "input_type": "start"
    },{
        onMessage:(data)=>{
          setMessages(
            [...messages,newMessage,{
              id: messages.length + 1,
              role: "ai",
              content: data?.message,
            }]
          )
          console.log("data",data)
        },
        onEnd:(data)=>{
          setMessages([...messages,newMessage,{
            id: messages.length + 1,
            role: "ai",
            content: data?.message,
          }])
 
        }
      });
    }
  };

  return (
    <div className={styles.chatApp}>
      <div className={styles.messageList}>
        {messages.map((message) => (
          <div
            key={message.id}
            className={`${styles.message} ${styles[message.role]}`}
          >
            <span className={styles.role}>
              {message.role === "user" ? "User" : "AI"}:
            </span>
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
        <button type="submit" className={styles.submitButton}>
          提问
        </button>
      </form>
    </div>
  );
};

export default ChatApp;
