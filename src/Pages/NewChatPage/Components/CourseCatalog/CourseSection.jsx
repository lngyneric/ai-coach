import classNames from "classnames";
import styles from "./CourseSection.module.scss";
import { SECTION_STATUS } from "constants/courseContants.js";

export const CourseSection = ({
  id,
  name = '',
  status = SECTION_STATUS.learning,
  selected,
  onSelect = ({ id }) => {},
}) => {
  const available = !status.unavailable;
  const genIconClassName = () => {
    switch (status) {
      case SECTION_STATUS.notStart:
      case SECTION_STATUS.unavailable:
        return styles.small;
      case SECTION_STATUS.learning:
      case SECTION_STATUS.completed:
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
        available ? styles.available : styles.unavailable
      )}
      onClick={() => onSelect({ id })}
    >
      <div className={classNames(styles.iconWrapper, genIconClassName())}>
        <div className={styles.topLine}></div>
        <div className={styles.icon}>
          {(status === SECTION_STATUS.notStart ||
            status === SECTION_STATUS.unavailable) && (
            <div className={styles.smallIcon}></div>
          )}
          {status === SECTION_STATUS.learning &&
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
          {status === SECTION_STATUS.completed &&
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
