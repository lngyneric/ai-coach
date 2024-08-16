import { Avatar } from 'antd';
import PopupModal from 'Components/PopupModal';
import styles from './SettingModal.module.scss';
import classNames from 'classnames';
import { useUserStore } from 'stores/useUserStore.js';
import { Modal } from 'antd';
import { memo } from 'react';
import userIcon from 'Assets/newchat/light/user.png';
import editIcon from 'Assets/newchat/light/icon16-edit.png';
import memberIcon from 'Assets/newchat/light/icon16-member.png';
import exitLoginIcon from 'Assets/newchat/light/exit-login-2x.png';
import { useCallback } from 'react';
import { useDisclosture } from 'common/hooks/useDisclosture.js';
import PayModal from '../Pay/PayModal.jsx';

export const SettingModal = ({
  open,
  onClose,
  style,
  onLoginClick = () => {},
  onGoToSetting = () => {},
  className,
}) => {
  const { hasLogin, userInfo, logout } = useUserStore((state) => state);

  const {
    open: payModalOpen,
    onOpen: onPayModalOpen,
    onClose: onPayModalClose,
  } = useDisclosture();

  const onLogoutClick = async (e) => {
    await Modal.confirm({
      title: '确认退出登录？',
      content: '确认退出登录么',
      onOk: async () => {
        await logout();
        onClose?.(e);
      },
    });
  };
  const avatar = userInfo?.avatar || userIcon;

  const onLoginRowClick = useCallback( () => {
    if (!hasLogin) {
      onLoginClick?.();
    } else {
      onGoToSetting?.();
    }
  }, [hasLogin, onGoToSetting, onLoginClick]);

  const onMemberRowClick = useCallback(() => {
    if (!hasLogin) {
      onLoginClick?.();
    } else {
      onPayModalOpen();
    }
  }, []) 

  return (
    <>
      <PopupModal
        open={open}
        onClose={onClose}
        wrapStyle={{ ...style }}
        className={className}
      >
        <div className={styles.settingModal}>
          <div
            className={classNames(styles.settingRow, styles.loginRow)}
            onClick={onLoginRowClick}
          >
            <div className={styles.loginLeft}>
              <Avatar src={avatar} size={20} />
              <div className={styles.userName}>
                {hasLogin ? userInfo?.name || '默认名称' : '未登录'}
              </div>
            </div>
            <img className={styles.rowIcon} src={editIcon} alt="" />
          </div>
          <div
            className={styles.settingRow}
            onClick={onMemberRowClick}
          >
            <div>会员管理</div>
            <img
              className={styles.rowIcon}
              src={memberIcon}
              alt=""
            />
          </div>
          {hasLogin && (
            <div className={styles.settingRow} onClick={onLogoutClick}>
              <div>退出登录</div>
              <img
                className={styles.rowIcon}
                src={exitLoginIcon}
                alt=""
              />
            </div>
          )}
        </div>
      </PopupModal>

      <PayModal
        open={payModalOpen}
        onCancel={onPayModalClose}
        onOk={onPayModalClose}
      />
    </>
  );
};

export default memo(SettingModal);
