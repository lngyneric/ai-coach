/**
 * 用户配置界面
 */
import styles from './UserSettings.module.scss';
import MainButton from 'Components/MainButton.jsx';

export const UserSettings = () => {
  const onSaveSettingsClick = () => {

  }

  return (
    <div className={styles.userSettings}>
      <div className={styles.settingHeader}></div>
      <div className={styles.settingBody}></div>
      <div className={styles.settingFooter}>
        <MainButton onClick={onSaveSettingsClick} >保存</MainButton>
      </div>
    </div>
  );
};

export default UserSettings
