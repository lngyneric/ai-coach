import '@chatui/core/dist/index.css';
import Chat, { Bubble, useMessages } from '@chatui/core';
import { Button, Image } from 'antd';
import { useEffect, forwardRef, useImperativeHandle, useState, useContext } from 'react';
import { runScript, getLessonStudyRecord } from '@Api/study';
import { ReactMarkdown } from 'react-markdown/lib/react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { CopyOutlined  } from '@ant-design/icons';
import { genUuid } from '@Utils/common.js';
import ChatInputArea from './ChatInput/ChatInputArea.jsx';
import { AppContext } from 'Components/AppContext.js';
import styles from './ChatComponents.module.scss';
import { INPUT_TYPE } from './ChatInput/ChatInputArea.jsx';
import { useCurrentLesson } from '@stores/useCurrentLesson';
import { SECTION_STATUS } from "constants/courseContants.js";

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

const createMessage = ({id = 0, role, content, type = 'text', userInfo }) => {
  const mid = id || genUuid();

  const position = role === USER_ROLE.STUDENT ? 'right' : 'left';

  let avatar = robotAvatar;

  if (role === USER_ROLE.STUDENT) {
    avatar = userInfo?.avatar || require('@Assets/newchat/light/user.png');
  }
  return {
    _id: mid,
    id: mid,
    role,
    content,
    type,
    position,
    user: {avatar},
  }
}

const convertMessage = (serverMessage, userInfo) => {
  return createMessage({
    id: serverMessage.id,
    role: serverMessage.script_role,
    content: serverMessage.script_content,
    type: serverMessage.script_type,
    userInfo,
  });
}

const convertInputModal = ({ type, content }) => {
  if (type === 'input') {
    return {
      type: INPUT_TYPE.TEXT,
      content: content,
    }
  } else if (type === INPUT_TYPE.BUTTONS){
    const buttons = content.buttons;
    if (buttons.length === 1) {
      return {
        type: INPUT_TYPE.CONTINUE,
        content: buttons[0].label,
        value: buttons[0].value,
      }
    } else {
      return {
        type,
        content,
      }
    }
  }
}

const ChatComponents = forwardRef(({ className, lessonUpdate, catalogId }, ref) => {
  const { messages, appendMsg, setTyping, updateMsg, resetList } = useMessages(
    [],
  );

  const [chatId, setChatId] = useState("");
  const { lessonId: currLessonId, changeCurrLesson } = useCurrentLesson(state => state);
  const [lessonId, setLessonId] = useState(null);
  const [scriptId, setScriptId] = useState("");
  const [inputPlaceholder, setInputPlaceholder] = useState("请输入");
  const [inputDisabled, setInputDisabled] = useState(false);
  const { userInfo } = useContext(AppContext);
  const [inputModal, setInputModal] = useState(null);

  useEffect(() => {
    if (!lessonId) {
      setLessonId(currLessonId);
    }
  }, [currLessonId])

  useEffect(() => {
    if (!catalogId) {
      return
    }

    (async () => {
      resetList();

      const resp = await getLessonStudyRecord(catalogId);
      const records = resp.data.records;
      const ui = resp.data.ui;

      if (!records || records.length === 0) {
        handleSend('start', '');
        return
      }

      records.forEach((v, i) => {
        const newMessage = convertMessage({
          ...v,
          id: i,
          script_type: 'text',
        }, userInfo);
        appendMsg(newMessage);
      });

      setLessonId(records[records.length - 1].lesson_id);

      if (ui) {
        const nextInputModal = convertInputModal(ui);
        setInputModal(nextInputModal);
      }

    })();  
  }, [catalogId]);

  const nextStep = ({ chatId, lessonId, val, type }) => {
    let lastMsg = null;
    runScript(chatId, lessonId, val, type, (response) => {
      try {
        if (response.type === "text") {
          if (lastMsg !== null && lastMsg.type === "text") {
            lastMsg.content = lastMsg.content + response.content;
            updateMsg(lastMsg.id, lastMsg);
          } else {
            const id = genUuid();
            lastMsg = createMessage({
              id: id,
              type: response.type,
              role: USER_ROLE.TEACHER,
              content: response.content,
              userInfo,
            })
            appendMsg(lastMsg);
          }
        } else if (response.type === "text_end") {
          lastMsg = null;
        } else if (response.type === "input") {
          setInputModal({ type: INPUT_TYPE.TEXT, content: response.content });
          // setLessonId(response.lesson_id);
          setInputDisabled(false);
        }else if (response.type === "buttons") {
          const model = convertInputModal(response)
          setInputModal(model)
        } else if (response.type === "study_complete") {
        } else if (response.type === "lesson_update") {
          const content = response.content;
          lessonUpdate?.({ id: content.lesson_id, name: content.lesson_name, status: content.status });

          if (content.status === SECTION_STATUS.PREPARE_LEARNING) {
            nextStep({ chatId, lessonId: content.lesson_id, type: 'start', val: '' })
          }
          if (content.status === SECTION_STATUS.LEARNING) {
            setLessonId(content.lesson_id);
            changeCurrLesson(content.lesson_id);
          }
        } else if (response.type === 'chapter_update') {
        }
      } catch (e) { }
    });
  }

  function handleSend(type, val) {
    console.log('handle send',type,val)
    if (type === "text" && val.trim()) {
      const message = createMessage({
        role: USER_ROLE.STUDENT,
        content: val,
        type: 'text',
        userInfo,
      });
      appendMsg(message);
    } else if (type === "button") {
    }
    setTyping(true);
    setInputModal(null);
    nextStep({ chatId, lessonId, type, val });
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
          id: genUuid(),
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
    // setLessonId(lessonInfo.lesson_id);
    setChatId(lessonInfo.course_id);
    if (lessonInfo.status === "未开始") {
          // handleSend("start","")
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
        renderBeforeMessageList={renderBeforeMessageList}
        recorder={{ canRecord: true }}
        placeholder={inputPlaceholder}
        inputOptions={{ disabled: inputDisabled }}
        Composer={({ onChange, onSubmit, value }) => {
          return<></> 
        }}
      />

      {
        (true && inputModal) &&
        <ChatInputArea
          type={inputModal.type}
          content={inputModal.content}
          onSend={(type, val) => {
            handleSend(type, val);
          }}
        />
      }
    </div>
  );
});

export default ChatComponents;
