import classNames from "classnames";
import styles from "./CourseSection.module.scss";
import { SECTION_STATUS } from "constants/courseContants.js";

export const CourseSection = ({
  id,
  name = '',
  status = SECTION_STATUS.LEARNING,
  selected,
  canLearning = false,
  onSelect = ({ id }) => {},
}) => {
  const genIconClassName = () => {
    switch (status) {
      case SECTION_STATUS.NOT_START:
      case SECTION_STATUS.LOCKED:
        return styles.small;
      case SECTION_STATUS.PREPARE_LEARNING:
      case SECTION_STATUS.LEARNING:
      case SECTION_STATUS.COMPLETED:
        return "";
      default:
        return styles.small;
    }
  };

  return (
    <div
      className={classNames(
        styles.courseSection,
        selected && styles.selected,
        canLearning ? styles.available : styles.unavailable
      )}
      onClick={() => onSelect({ id })}
    >
      <div className={classNames(styles.iconWrapper, genIconClassName())}>
        <div className={styles.topLine}></div>
        <div className={styles.icon}>
          {(status === SECTION_STATUS.NOT_START ||
            status === SECTION_STATUS.LOCKED) && (
            <div className={styles.smallIcon}></div>
          )}
          {(status === SECTION_STATUS.LEARNING || status === SECTION_STATUS.PREPARE_LEARNING) &&
            (selected ? (
              <img
                className={styles.bigIcon}
                src={require("@Assets/newchat/light/icon16-learning-selected.png")}
                alt=""
              />
            ) : (
              <img
                className={styles.bigIcon}
                src={require("@Assets/newchat/light/icon16-learning.png")}
                alt=""
              />
            ))}
          {status === SECTION_STATUS.COMPLETED &&
            (selected ? (
              <img
                className={styles.bigIcon}
                src={require("@Assets/newchat/light/icon16-learning-completed-selected.png")}
                alt=""
              />
            ) : (
              <img
                className={styles.bigIcon}
                src={require("@Assets/newchat/light/icon16-learning-completed.png")}
                alt=""
              />
            ))}
        </div>
        <div className={styles.bottomLine}></div>
      </div>
      <div className={styles.textArea}>
        <div className={styles.label}>{status}</div>
        <div className={styles.courseTitle}>
          {name}
        </div>
      </div>
    </div>
  );
};

export default CourseSection;
