import MainButton from "Components/MainButton.jsx";
import styles from './ChatButtonGroup.module.scss';

/**
 * 聊天按钮组控件
 */
export const ChatButtonGroup = ({ buttons = [], onClick = (val) => {} }) => {
  return (
    <div className={styles.ChatButtonGroup}>
      {
        buttons.map((e) => {
          return <MainButton
            key={e.id}
            onClick={() => onClick?.(e.value)}
            style={{margin: '10px 0 0 10px'}}
          >{e.label}</MainButton>
        })
      }
    </div>
  );
}

export default ChatButtonGroup;
