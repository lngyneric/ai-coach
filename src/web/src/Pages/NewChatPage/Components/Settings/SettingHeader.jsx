import { Breadcrumb } from 'antd';
import styles from './SettingHeader.module.scss';
import classNames from 'classnames';

export const SettingHeader = ({ className, onHomeClick }) => {
  return (
    <div className={classNames(styles.settingHeader, className)}>
      <Breadcrumb
        items={[
          {
            title: (
              <span className={styles.clickable} onClick={onHomeClick}>
                主页
              </span>
            ),
          },
          { title: <span>个人信息</span> },
        ]}
      />
    </div>
  );
};

export default SettingHeader;
