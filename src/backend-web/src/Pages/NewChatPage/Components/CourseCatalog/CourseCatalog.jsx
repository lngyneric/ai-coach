import classNames from 'classnames';
import CourseSection from './CourseSection.jsx';
import styles from './CourseCatalog.module.scss'

import { useState } from 'react';

export const CourseCatalog = ({ id = 0, chapterList = [{id: 0}], onCollapse=({id, collapse}) => {} }) => {
  const [collapse, setCollapse] = useState(false);

  const onCollapseHandler = (e) => {
    console.log('onCollapseHandler');
    setCollapse(!collapse)
  }

  return (<div className={styles.courseCatalog}>
    <div className={styles.titleRow} onClick={onCollapseHandler}>
      <div>第一章</div>
      <img className={classNames(styles.collapseBtn, collapse ? styles.collapse : '')} src={require('@Assets/newchat/light/icon16-arrow-down.png')} alt="" />
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
