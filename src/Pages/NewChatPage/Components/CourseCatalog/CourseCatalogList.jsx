// 课程目录
import CourseCatalog from "./CourseCatalog.jsx";
import styles from './CourseCatalogList.module.scss';

export const CourseCatalogList = ({ catalogs = [{ id: 1 }, {id: 2}, {id: 3}] }) => {
  return (<div className={styles.courseCatalogList}>
    <div className={styles.titleRow}>
      <div className={styles.titleArea}>
        <img className={styles.icon} src={require('@Assets/newchat/light/icon16-course-list.png')} alt="课程列表" />
        <div className={styles.titleName}>课程列表</div>
      </div>
      <div className={styles.chapterCount}>80节/10章</div>
    </div>
    <div className={styles.listRow}>
      {catalogs.map((catalog) => {
        return <CourseCatalog key={catalog.id} />
      })}
    </div>

  </div>)
};

export default CourseCatalogList;
