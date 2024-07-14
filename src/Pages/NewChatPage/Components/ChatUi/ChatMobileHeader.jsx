import styles from './ChatMobileHeader.module.scss';

export const ChatMobileHeader = (props) => {
  return <div className={styles.ChatMobileHeader}>
    <image src={require('@Assets/logos/logo-hori-84.png')} />
  </div>
}

export default ChatMobileHeader;
