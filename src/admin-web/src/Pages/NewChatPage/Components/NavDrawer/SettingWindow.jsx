import PopupModal from '@Components/PopupModal';
import styles from './SettingWindow.module.scss';
import classNames from 'classnames';

import Icon1 from '@Assets/newchat/light/icon16-edit.svg';
import { redirect } from 'react-router-dom';

export const SettingWindow = ({ open, onClose, style }) => {
  return (
    <PopupModal open={open} onClose={onClose} wrapStyle={{ ...style}}>
      <div className={styles.settingWindow}>
        <div className={classNames(styles.settingRow, styles.loginRow)}>
          <div className={styles.loginLeft}>
            <div>x</div>
            <div>未登录</div>
          </div>
          <img src={Icon1} style={{ color: 'red' }} />
        </div>
        <div className={styles.settingRow}>
          <div>账号安全</div>
          <img
            className={styles.rowIcon}
            src={require('@Assets/newchat/light/icon16-account.png')}
            alt=''
          />
        </div>
        <div className={styles.settingRow}>
          <div>会员管理</div>
          <img
            className={styles.rowIcon}
            src={require('@Assets/newchat/light/icon16-member.png')}
            alt=''
          />
        </div>
      </div>
    </PopupModal>
  )
}

export default SettingWindow;
