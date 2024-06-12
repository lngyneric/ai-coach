/**
 * 用户配置界面
 */
import styles from './UserSettings.module.scss';
import MainButton from 'Components/MainButton.jsx';
import SettingHeader from './SettingHeader.jsx';
import { Form } from 'antd';


export const UserSettings = ({ onClose }) => {
  const [form] = Form.useForm()
  const onSaveSettingsClick = () => {
  };

  return (
    <div className={styles.userSettings}>
      <SettingHeader onBackClick={onClose} />
      <div className={styles.settingBody}>
        <div className={styles.centerWrapper}>
          <Form form={form} className={styles.formWrapper}>
            <Form.Item></Form.Item>
          </Form>
        </div>
      </div>
      <div className={styles.settingFooter}>
        <div className={styles.centerWrapper}>
          <MainButton onClick={onSaveSettingsClick} >保存</MainButton>
        </div>
      </div>
    </div>
  );
};

export default UserSettings
