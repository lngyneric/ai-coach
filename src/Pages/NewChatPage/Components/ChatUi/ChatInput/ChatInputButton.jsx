import { INPUT_SUB_TYPE, INPUT_TYPE } from 'constants/courseContants.js';
import styles from './ChatInputButton.module.scss';
import MainButton from 'Components/MainButton.jsx';

export const ChatInputButton = ({ type, subType, props, onClick }) => {
  return (
    <MainButton className={styles.continueBtn} width="90%" onClick={() => {
      if (!subType) {
        onClick?.(INPUT_TYPE.CONTINUE, props.value);
      } else if (subType === INPUT_SUB_TYPE.NEXT_CHAPTER) {
        onClick?.(INPUT_TYPE.ACTION, { action: INPUT_SUB_TYPE.NEXT_CHAPTER, lessonId: props.lessonId });
      }
    }}>{props.label}</MainButton>
  );
}

export default ChatInputButton;
