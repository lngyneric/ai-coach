import styles from  './NavFooter.module.scss';
import { ApartmentOutlined } from '@ant-design/icons';
import classNames from 'classnames';

export const NavFooter = ({ 
  isCollapse = false,
  onFilingClick = () => {},
  onThemeClick = () => {},
  onSettingsClick = () => {},
}) => {
  return (<div className={classNames(styles.navFooter, isCollapse ? styles.collapse : '') }>
    <div className={styles.settingBtn} onClick={onFilingClick} >
      <img src={require('@Assets/newchat/light/icon16-filing.png')} className={styles.icon} alt="备案" />
      <div className={styles.btnText}>备案</div>
    </div>
    <div className={styles.settingBtn} onClick={onThemeClick}>
      <img src={require('@Assets/newchat/light/icon16-theme.png')} className={styles.icon} alt="备案" />
      <div className={styles.btnText}>皮肤</div>
    </div>
    <div className={styles.settingBtn} onClick={onSettingsClick}>
      <img src={require('@Assets/newchat/light/icon16-setting.png')} className={styles.icon} alt="备案" />
      <div className={styles.btnText}>设置</div>
    </div>
  </div>);
}

export default NavFooter;
