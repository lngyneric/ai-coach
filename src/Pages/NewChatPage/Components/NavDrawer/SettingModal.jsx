import PopupModal from '@Components/PopupModal';
import styles from './SettingModal.module.scss';
import classNames from 'classnames';
import Icon1 from '@Assets/newchat/light/icon16-edit.svg';
import { useUserStore } from '@stores/useUserStore.js';
import { Modal } from 'antd';


export const SettingModal = ({ open, onClose, style }) => {
  const { hasLogin, logout } = useUserStore((state) => state);
  const [modal] = Modal.useModal();

  const onLogoutClick = async () => {
    const confirmed = await modal.confirm({
      title: '确认退出登录？',
      content: '确认退出登录么',
    });
    if (confirmed) {
      await logout();
      onClose();
    }
  };

  return (
    <PopupModal open={open} onClose={onClose} wrapStyle={{ ...style}}>
      <div className={styles.settingModal}>
        <div className={classNames(styles.settingRow, styles.loginRow)}>
          <div className={styles.loginLeft}>
            <div>x</div>
            <div>未登录</div>
          </div>
          <img src={Icon1} alt="" />
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
        {
          hasLogin &&
          <div className={styles.settingRow} onClick={onLogoutClick}>
            <div>退出登录</div>
            <img
              className={styles.rowIcon}
              src={require('@Assets/newchat/light/icon16-member.png')}
              alt=''
            />
          </div>
        }
      </div>
    </PopupModal>
  )
}

export default SettingModal;
