import { Avatar } from 'antd';
import PopupModal from '@Components/PopupModal';
import styles from './SettingModal.module.scss';
import classNames from 'classnames';
import Icon1 from '@Assets/newchat/light/icon16-edit.svg';
import { useUserStore } from '@stores/useUserStore.js';
import { Modal } from 'antd';

import SexSettingModal from '../Settings/SexSettingModal.jsx';
import BirthdaySettingModal from '../Settings/BirthdaySettingModal.jsx';
import { useState } from 'react';

export const SettingModal = ({
  open,
  onClose,
  style,
  onLoginClick = () => {},
  className,
}) => {
  const { hasLogin, userInfo, logout } = useUserStore((state) => state);
  const [tryOpen, setTryOpen] = useState(false);

  const onLogoutClick = async () => {
    await Modal.confirm({
      title: '确认退出登录？',
      content: '确认退出登录么',
      onOk: async () => {
        await logout();
        onClose();
      },
    });
  };
  const avatar = userInfo?.avatar || require('@Assets/newchat/light/user.png');

  const onTryOk = (val) => {
    console.log('onTryOk', val);
  };

  const onLoginRowClick = () => {
    if (!hasLogin) {
      onLoginClick?.();
    }
  };

  return (
    <>
      <BirthdaySettingModal
        open={tryOpen}
        onClose={() => {
          setTryOpen(false);
        }}
        onOk={(v) => onTryOk(v)}
      />

      <PopupModal open={open} onClose={onClose} wrapStyle={{ ...style }} className={className}>
        <div className={styles.settingModal}>
          <div
            className={classNames(styles.settingRow, styles.loginRow)}
            onClick={onLoginRowClick}
          >
            <div className={styles.loginLeft}>
              <Avatar src={avatar} size={20} />
              <div className={styles.userName}>
                {hasLogin ? userInfo?.name || '' : '未登录'}
              </div>
            </div>
            <img src={Icon1} alt="" />
          </div>
          <div className={styles.settingRow}>
            <div>账号安全</div>
            <img
              className={styles.rowIcon}
              src={require('@Assets/newchat/light/icon16-account.png')}
              alt=""
            />
          </div>
          <div
            className={styles.settingRow}
            onClick={() => {
              setTryOpen(true);
            }}
          >
            <div>会员管理</div>
            <img
              className={styles.rowIcon}
              src={require('@Assets/newchat/light/icon16-member.png')}
              alt=""
            />
          </div>
          {hasLogin && (
            <div className={styles.settingRow} onClick={onLogoutClick}>
              <div>退出登录</div>
              <img
                className={styles.rowIcon}
                src={require('@Assets/newchat/light/icon16-member.png')}
                alt=""
              />
            </div>
          )}
        </div>
      </PopupModal>
    </>
  );
};

export default SettingModal;
