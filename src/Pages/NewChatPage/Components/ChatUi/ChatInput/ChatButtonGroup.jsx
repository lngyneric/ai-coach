import MainButton from "Components/MainButton.jsx";
import styles from './ChatButtonGroup.module.scss';

/**
 * 聊天按钮组控件
 */
export const ChatButtonGroup = ({ buttons = [
  {label: '按钮1', value: 'b1'},
  {label: '按钮2', value: 'b2'},
  {label: '按钮3', value: 'b3'},
  {label: '按钮4', value: 'b4'},
  {label: '按钮5', value: 'b5'},
  {label: '按钮y', value: 'b6'},
], onClick = (val) => {} }) => {
  return (
    <div className={styles.ChatButtonGroup}>
      {
        buttons.map((e) => {
          return <MainButton key={e.id} onClick={onClick?.(e.value)} className={styles.selectBtn} >{e.label}</MainButton>
        })
      }
    </div>
  );
}
