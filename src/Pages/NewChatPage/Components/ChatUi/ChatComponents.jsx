import Chat, { Bubble, useMessages, Empty, Card, CardMedia, CardTitle, CardText, CardActions } from "@chatui/core";
import { Button } from "antd";
import { Image } from "antd";

import "@chatui/core/dist/index.css";
import { useEffect, forwardRef, useImperativeHandle, useState } from "react";
// import { SendMsg } from "../../Service/SSE";
import { runScript, getLessonStudyRecord } from "@Api/study";
import { UploadEvent } from "@Api/UploadEvent";
import { ReactMarkdown } from "react-markdown/lib/react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { CopyOutlined, NodeExpandOutlined, SendOutlined } from "@ant-design/icons";
import { genUuid } from '@Utils/common.js';
import ChatInputArea from "./ChatInput/ChatInputArea.jsx";
import styles from './ChatComponents.module.scss';
import { useContext } from "react";
import { AppContext } from "Components/AppContext.js";

const USER_ROLE = {
  TEACHER: '老师',
  STUDENT: '学生'
};

const robotAvatar = require("@Assets/chat/sunner_icon.jpg");

const MarkdownBubble = (props) => {
  const onCopy = (content) => {
    navigator.clipboard.writeText(content);
  };

  return (
    <Bubble>
      <ReactMarkdown
        children={props.content}
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            return !inline && match ? (
              <div
                className="markdown-code_block"
                style={{
                  position: "relative",
                }}
              >
                <Button
                  className="copy_btn"
                  type="dashed"
                  ghost
                  size="small"
                  icon={<CopyOutlined></CopyOutlined>}
                  onClick={() => onCopy(children)}
                ></Button>
                <SyntaxHighlighter
                  {...props}
                  children={String(children).replace(/\n$/, "")}
                  style={vscDarkPlus}
                  language={match[1]}
                  showLineNumbers={true}
                  wrapLines={false}
                  onCopy={() => {
                    onCopy(children);
                  }}
                  renderInline={true}
                ></SyntaxHighlighter>
              </div>
            ) : (
              <code {...props} className={className}>
                {children}
              </code>
            );
          },
          img(props) {
            return <Image {...props} width={320}></Image>;
          },
        }}
      ></ReactMarkdown>
    </Bubble>
  );
};

const convertMessage = (serverMessage, userInfo) => {
  const role = serverMessage.script_role;
  let avatar = robotAvatar;

  if (role === USER_ROLE.STUDENT) {
    avatar = userInfo?.avatar || require('@Assets/newchat/light/user.png');
  }

  return {
    role,
    content: serverMessage.script_content,
    id: serverMessage.id,
    type: serverMessage.script_type,
    position: role === USER_ROLE.STUDENT ? 'right' : 'left',
    user: { avatar },
  }
}

const ChatComponents = forwardRef(({ className ,lessonStatusUpdate, catalogId }, ref) => {
  const { messages, appendMsg, setTyping, updateMsg, resetList } = useMessages(
    [],
  );

  const [chatId, setChatId] = useState("");
  const [lessonId, setLessonId] = useState("");
  const [scriptId, setScriptId] = useState("");
  const [inputPlaceholder, setInputPlaceholder] = useState("请输入");
  const [inputDisabled, setInputDisabled] = useState(false);
  const { userInfo } = useContext(AppContext);
  const [inputModal, setInputModal] = useState(null);

  useEffect(() => {
    if (!catalogId) {
      return
    }
    (async () => {
      resetList();

      const resp = await getLessonStudyRecord(catalogId);
      const records = resp.data.records;

      if (!records || records.length === 0) {
        handleSend('start', '');
        return
      }

      records.forEach((v, i) => {
        v.id = i;
        const newMessage = convertMessage({
          ...v,
          id: i,
          script_type: 'text',
        }, userInfo);
        appendMsg(newMessage);

        console.log('load', newMessage);
      });

    })();  
  }, [catalogId]);

  const nextStep = ({ chatId, lessonId, val, type }) => {
    let lastMsg = null;
    runScript(chatId, lessonId, val, type, (response) => {
      try {
        setChatId(response.chat_id);
        let id = genUuid();
        if (response.type === "text") {
          if (lastMsg !== null && lastMsg.content.type === "text") {
            lastMsg.content.text = lastMsg.text + response.content;
            updateMsg(lastMsg.id, lastMsg);
          } else {
            lastMsg = {
              id: id,
              type: response.type,
              text: response.content,
              position: "left",
              user: { avatar: robotAvatar },
            };
            appendMsg(lastMsg);
          }
        } else if (response.type === "text_end") {
          lastMsg = null;
        } else if (response.type === "input") {
          setInputPlaceholder(response.content);
          setScriptId(response.id);
          setInputDisabled(false);
        } else if (response.type === "button") {
          lastMsg = {
            _id: id,
            type: "card",
            content: response.content,
            position: "right"
          };
          appendMsg(lastMsg);
          setInputDisabled(true);
        }else if (response.type === "buttons") {
          console.log(response)
          lastMsg = {
            _id: id,
            type: "card",
            content: response.content,
            position: "right"
          };
          appendMsg(lastMsg);
          setInputDisabled(true); 
          
        } else if (response.type === "study_complete") {
          // setLessonId(response.lesson_id);

        } else if (response.type === "lesson_update"){
            if (lessonStatusUpdate){
              lessonStatusUpdate(response.content)
            }
        }
      } catch (e) { }
    });
  }

  function handleSend(type, val) {
    console.log('handle send',type,val)
    let sendScriptId = scriptId;
    if (type === "text" && val.trim()) {
      appendMsg({
        _id: genUuid(),
        type: "text",
        content: { type: "text", text: val },
        position: "right",
      });
      UploadEvent("ChatInput", {
        text_length: val.length,
        page: "chat",
      });
    } else if (type === "button") {
      sendScriptId = undefined;
    }
    setTyping(true);
    nextStep({ chatId, lessonId, val, type });
  }

  function onButtonClick(type,content) {
    handleSend(type, content);
  }
  function renderMessageContent(msg) {
    const { content, type } = msg;
    if (content === undefined) {
      return null;
    }
    if (type === "calling") {
      return (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            padding: "10px",
            borderRadius: "5px",
            fontWeight: "bold",
            minWidth: "25%",
            backgroundColor: "#f7f8fa",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <img
                style={{ display: content.isProcessed ? "block" : "none" }}
                src={require("@Assets/success_chat.png")}
                alt=""
              />
              <img
                className="chat_loading"
                style={{ display: content.isProcessed ? "none" : "block" }}
                src={require("@Assets/loading_chat.png")}
                alt=""
              />
              {content.isProcessed
                ? "操作执行完成"
                : `正在执行操作:“${content.function_name}”`}
            </div>
          </div>
        </div>
      );
    } else if (type === "text") {
      return <MarkdownBubble content={content} />;
    } 
    return null;
  }

  function loadMsg(chatId, newMessages) {
    resetList()
    if (newMessages === undefined || newMessages === null) {
      return;
    }
    
    newMessages.forEach((item) => {
      if (item.role === "学生") {
        appendMsg({
          _id: genUuid(),
          type: "text",
          content: { type: "text", text: item.content },
          position: "right",
        });
      } else {
        if (item.function_call) {
          appendMsg({
            content: {
              function_name: item.function_call,
              type: "calling",
              isProcessed: true,
            },
            _id: genUuid(),
          });
        } else {
          appendMsg({
            _id: genUuid(),
            type: "text",
            content: { type: "text", text: item.content },
            position: "left",
            user: { avatar: require("@Assets/chat/sunner_icon.jpg") },
          });
        }
      }
    });

  }
  function checkResetListComplete() {
    return new Promise((resolve) => {
      const intervalId = setInterval(() => {
        if (messages !== undefined && messages !== null && messages.length === 0) {
          clearInterval(intervalId);
          resolve();
        }
      }, 100);
    });
  }

  const switchLesson = async (lessonInfo) => {
    setLessonId(lessonInfo.lesson_id);
    setChatId(lessonInfo.course_id);
    if (lessonInfo.status === "未开始") {
          handleSend("start","")
    } else {
      await getLessonStudyRecord(lessonInfo.lesson_id).then((res) => {
        // console.log("getLessonStudyRecord", res);
        loadMsg(lessonInfo.lesson_id, res.data);
      });
      loadMsg()
    }
  }

  useImperativeHandle(ref, () => ({
    loadMsg,
    switchLesson
  }));

  function renderBeforeMessageList() {
    // message 的长度等于 0 的时候 返回 Empty 组件
    if (messages.length === 0) {
      return (
        <div
          className="full-height chat-ui_container"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
        </div>
      );
    }
  }
  return (
    <div className={styles.chatComponents} >
      <Chat
        navbar={null}
        messages={messages}
        renderMessageContent={renderMessageContent}
        onSend={handleSend}
        loadMsg={loadMsg}
        renderBeforeMessageList={renderBeforeMessageList}
        recorder={{ canRecord: true }}
        placeholder={inputPlaceholder}
        inputOptions={{ disabled: inputDisabled }}
        Composer={({ onChange, onSubmit, value }) => {
          return<></> 
        }}
      />

      {
        (!inputDisabled && inputModal) &&
        <ChatInputArea />
      }
    </div>
  );
});

export default ChatComponents;
