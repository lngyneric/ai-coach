import ChatInput from "./ChatInput"

/**
 * 聊天区的整体画布
 */
export const ChatUi = (props) => {
  return (<div style={
    {
      height: '100%',
      background: '#F8FBFC',
      flex: '1 1 auto',
    }
  }>
    <ChatInput/>
  </div>);
};

export default ChatUi;
