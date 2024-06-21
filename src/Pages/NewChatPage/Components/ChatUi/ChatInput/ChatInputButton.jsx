import {
  INTERACTION_OUTPUT_TYPE,
  INTERACTION_TYPE,
} from 'constants/courseContants.js';
import styles from './ChatInputButton.module.scss';
import MainButton from 'Components/MainButton.jsx';

export const ChatInputButton = ({ type, props, onClick, disabled }) => {
  return (
    <div className={styles.continueWrapper}>
      <MainButton
        className={styles.continueBtn}
        width="90%"
        disabled={disabled}
        onClick={() => {
          if (type === INTERACTION_TYPE.NEXT_CHAPTER) {
            onClick?.(INTERACTION_OUTPUT_TYPE.NEXT_CHAPTER, {
              lessonId: props.lessonId,
            });
            return;
          }

          if (type === INTERACTION_TYPE.ORDER) {
            onClick?.(INTERACTION_OUTPUT_TYPE.ORDER, { orderId: props.value });
            return
          }

          onClick?.(INTERACTION_OUTPUT_TYPE.CONTINUE, props.value);
        }}
      >
        {props.label}
      </MainButton>
    </div>
  );
};

export default ChatInputButton;
