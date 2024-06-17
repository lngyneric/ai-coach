import classNames from "classnames";
import CourseSection from "./CourseSection.jsx";
import styles from "./CourseCatalog.module.scss";

import { useState } from "react";

export const CourseCatalog = ({
  id = 0,
  name = "",
  chapters = [],
  collapse = false,
  onCollapse = ({ id }) => {},
  onChapterSelect = ({ id }) => {},
}) => {
  return (
    <div
      className={classNames(styles.courseCatalog, collapse && styles.collapse)}
    >
      <div className={styles.titleRow} onClick={() => onCollapse?.({id})}>
        <div>{name}</div>
        <img
          className={styles.collapseBtn}
          src={require("@Assets/newchat/light/icon16-arrow-down.png")}
          alt=""
        />
      </div>
      <div className={styles.sectionList}>
        {chapters.map((e) => {
          return (
            <CourseSection
              key={e.id}
              id={e.id}
              name={e.name}
              status={e.status}
              selected={e.selected}
              canLearning={e.canLearning}
              onSelect={onChapterSelect}
            />
          );
        })}
      </div>
    </div>
  );
};

export default CourseCatalog;
