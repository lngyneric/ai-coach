import ChatInput from "./ChatInput"

/**
 * 聊天区的整体画布
 */
export const ChatUi = ({ catalogId }) => {
  return (<div style={
    {
      height: '100%',
      background: '#F8FBFC',
      flex: '1 1 auto',
    }
  }>
    <ChatInput catalogId={catalogId} />
  </div>);
};

export default ChatUi;
