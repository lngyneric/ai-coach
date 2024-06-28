/**
 * 用户配置界面
 */
import styles from './UserSettings.module.scss';
import MainButton from 'Components/MainButton.jsx';
import SettingHeader from './SettingHeader.jsx';
import { Form } from 'antd';
import classNames from 'classnames';
import ChangeAvatar from './ChangeAvatar.jsx';

export const UserSettings = ({ onClose, className }) => {
  const [form] = Form.useForm();
  const onSaveSettingsClick = () => {};

  return (
    <>
      <div className={classNames(styles.UserSettings, className)}>
        <SettingHeader onBackClick={onClose} className={styles.settingHeader} />
        <div className={styles.settingBody}>
          <div className={styles.centerWrapper}>
            <ChangeAvatar img={''} />
            <div className={styles.basicInfoTitle}>基础信息</div>
            <div className={styles.settingInput}>
              <div className={styles.inputTitle}>昵称</div>
              <input
                type="text"
                className={styles.inputElement}
                placeholder="请输入姓名"
              />
            </div>
            <div className={classNames(styles.settingSelect, styles.inputUnit)}>
              <input
                type="text"
                className={styles.inputElement}
                placeholder="请输入性别"
                disabled={true}
              />
              <img
                className={styles.icon}
                src={require('@Assets/newchat/light/icon16-arrow-down.png')}
                alt="icon"
              />
            </div>
            <div className={classNames(styles.settingSelect, styles.inputUnit)}>
              <input
                type="text"
                className={styles.inputElement}
                placeholder="请选择生日"
                disabled={true}
              />
              <img
                className={styles.icon}
                src={require('@Assets/newchat/light/icon16-arrow-down.png')}
                alt="icon"
              />
            </div>
            <div className={classNames(styles.settingSelect, styles.inputUnit)}>
              <input
                type="text"
                className={styles.inputElement}
                placeholder="请选择行业"
                disabled={true}
              />
              <img
                className={styles.icon}
                src={require('@Assets/newchat/light/icon16-arrow-down.png')}
                alt="icon"
              />
            </div>
            <div className={classNames(styles.settingSelect, styles.inputUnit)}>
              <input
                type="text"
                className={styles.inputElement}
                placeholder="请选择职业"
                disabled={true}
              />
              <img
                className={styles.icon}
                src={require('@Assets/newchat/light/icon16-arrow-down.png')}
                alt="icon"
              />
            </div>
          </div>
        </div>
        <div className={styles.settingFooter}>
          <div className={styles.centerWrapper}>
            <MainButton
              className={styles.saveBtn}
              onClick={onSaveSettingsClick}
            >
              保存
            </MainButton>
          </div>
        </div>
      </div>
    </>
  );
};

export default UserSettings;
