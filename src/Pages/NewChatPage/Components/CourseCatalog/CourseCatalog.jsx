import classNames from 'classnames';
import CourseSection from './CourseSection.jsx';
import styles from './CourseCatalog.module.scss'

import { useState } from 'react';

export const CourseCatalog = ({ id = 0, chapterList = [{id: 0, available: true }, {id: 1, selected: true, available: true }, {id: 2}], onCollapse=({id, collapse}) => {} }) => {
  const [collapse, setCollapse] = useState(false);

  const onCollapseClick = (e) => {
    setCollapse(!collapse)
  }

  return (<div className={classNames(styles.courseCatalog, collapse && styles.collapse) }>
    <div className={styles.titleRow} onClick={onCollapseClick}>
      <div>第一章</div>
      <img className={styles.collapseBtn} src={require('@Assets/newchat/light/icon16-arrow-down.png')} alt="" />
    </div>
    <div className={styles.sectionList}>
      {
        chapterList.map(e => {
          return (<CourseSection key={e.id} {...e} />)
        })
      }
    </div>


  </div>)
}

export default CourseCatalog;
