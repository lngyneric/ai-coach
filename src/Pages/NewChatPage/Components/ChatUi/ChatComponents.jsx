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
import { INPUT_TYPE } from '@constants/courseContants.js';
import { useCurrentLesson } from '@stores/useCurrentLesson';
import { INPUT_SUB_TYPE, LESSON_STATUS } from "constants/courseContants.js";

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
      props: {content},
    }
  } else if (type === INPUT_TYPE.BUTTONS){
    const buttons = content.buttons;
    if (buttons.length === 1) {
      return {
        type: INPUT_TYPE.CONTINUE,
        props: {
          ...buttons[0],
        },
      }
    } else {
      return {
        type,
        props: content,
      }
    }
  }
}

const ChatComponents = forwardRef(({ className, lessonUpdate, onGoChapter = (id) => {}, chapterId }, ref) => {
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
  const [lessonEnd, setLessonEnd] = useState(false);

  useEffect(() => {
    if (!lessonId) {
      setLessonId(currLessonId);
    }
  }, [currLessonId])

  useEffect(() => {
    if (!chapterId) {
      return
    }

    (async () => {
      resetList();

      const resp = await getLessonStudyRecord(chapterId);
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
  }, [chapterId]);


  const lessonUpdateResp = (response) => {
    const content = response.content;
    lessonUpdate?.({ id: content.lesson_id, name: content.lesson_name, status: content.status });

    if (content.status === LESSON_STATUS.PREPARE_LEARNING) {
      nextStep({ chatId, lessonId: content.lesson_id, type: 'start', val: '' });
    }
    if (content.status === LESSON_STATUS.LEARNING) {
      setLessonId(content.lesson_id);
      changeCurrLesson(content.lesson_id);
    }
  }

  const nextStep = ({ chatId, lessonId, val, type }) => {
    let lastMsg = null;
    runScript(chatId, lessonId, val, type, (response) => {
      try {
        if (response.type === "text") {
          if (lessonEnd) {
            return
          }
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
          setInputModal({ type: INPUT_TYPE.TEXT, props: response });
          setInputDisabled(false);
        }else if (response.type === "buttons") {
          const model = convertInputModal(response)
          setInputModal(model)
        } else if (response.type === "study_complete") {
        } else if (response.type === "lesson_update") {
          lessonUpdateResp(response);
        } else if (response.type === 'chapter_update') {
          const { status, lesson_id: lessonId }  = response.content;
          if (status === LESSON_STATUS.COMPLETED) {
            setLessonEnd(true);
          }
          if (status === LESSON_STATUS.PREPARE_LEARNING) {
            setInputModal({
              type: INPUT_TYPE.CONTINUE,
              subType: INPUT_SUB_TYPE.NEXT_CHAPTER,
              props: {
                label: '继续',
                lessonId,
              }
            });
          }
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

  const renderMessageContent = (msg) => {
    const { content, type } = msg;
    if (content === undefined) {
      return <></>;
    }
    if (type === 'text') {
      return <MarkdownBubble content={content} />;
    } 
    return <></>;
  }


  useImperativeHandle(ref, () => ({
  }));

  const renderBeforeMessageList = () => {
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

  const onChatInputSend = (type, val) => {
    if (type === INPUT_TYPE.ACTION) {
      const { action } = val;
      if (action === INPUT_SUB_TYPE.NEXT_CHAPTER) {
        onGoChapter?.(val.lessonId);
      }
    } else {
      handleSend(type, val);
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
          props={inputModal.props}
          onSend={(type, val) => {
            onChatInputSend(type, val);
          }}
        />
      }
    </div>
  );
});

export default ChatComponents;
