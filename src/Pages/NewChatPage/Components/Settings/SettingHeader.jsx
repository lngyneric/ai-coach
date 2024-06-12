import { Button, Breadcrumb } from 'antd';

import styles from './SettingHeader.module.scss';

export const SettingHeader = ({ onBackClick }) => {
  return (
    <div className={styles.settingHeader}>
      <Breadcrumb items={[
        { title: <Button type="link" onClick={onBackClick}>主页</Button> },
        { title: '个人信息' },
      ]}/>
    </div>
  )
}

export default SettingHeader;
