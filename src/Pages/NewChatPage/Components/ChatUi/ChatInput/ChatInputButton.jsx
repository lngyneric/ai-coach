import { INTERACTION_OUTPUT_TYPE, INTERACTION_TYPE } from 'constants/courseContants.js';
import styles from './ChatInputButton.module.scss';
import MainButton from 'Components/MainButton.jsx';

export const ChatInputButton = ({ type, subType, props, onClick }) => {
  return (
    <div className={styles.continueWrapper}>
      <MainButton className={styles.continueBtn} width="90%" onClick={() => {
        if (type === INTERACTION_TYPE.NEXT_CHAPTER) {
          onClick?.(INTERACTION_OUTPUT_TYPE.NEXT_CHAPTER, { lessonId: props.lessonId });
          return
        }

        onClick?.(INTERACTION_OUTPUT_TYPE.CONTINUE, props.value);
      }}>{props.label}</MainButton>
    </div>
  );
}

export default ChatInputButton;
