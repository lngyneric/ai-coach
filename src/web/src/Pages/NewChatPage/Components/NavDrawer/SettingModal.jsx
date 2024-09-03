import { Avatar } from 'antd';
import { AppContext } from 'Components/AppContext.js';
import PopupModal from 'Components/PopupModal';
import styles from './SettingModal.module.scss';
import classNames from 'classnames';
import { useUserStore } from 'stores/useUserStore.js';
import { Modal } from 'antd';
import { memo, useCallback, useContext } from 'react';
import userIcon from 'Assets/newchat/light/user.png';
import editIcon from 'Assets/newchat/light/icon16-edit.png';
import memberIcon from 'Assets/newchat/light/icon16-member.png';
import exitLoginIcon from 'Assets/newchat/light/exit-login-2x.png';
import { useDisclosture } from 'common/hooks/useDisclosture.js';
import PayModal from '../Pay/PayModal.jsx';
import PayModalM from '../Pay/PayModalM.jsx';
import { useTranslation } from 'react-i18next';

export const SettingModal = ({
  open,
  onClose,
  onNavClose = () => {},
  style,
  onLoginClick = () => {},
  onGoToSetting = () => {},
  className,
}) => {
  const { t } = useTranslation();
  const { hasLogin, userInfo, logout, refreshUserInfo  } = useUserStore((state) => state);
  const { mobileStyle } = useContext(AppContext);

  const {
    open: payModalOpen,
    onOpen: onPayModalOpen,
    onClose: onPayModalClose,
  } = useDisclosture();

  const onLogoutClick = async (e) => {
    await Modal.confirm({
      title: t('user.confirmLogoutTitle'),
      content: t('user.confirmLogoutContent'),
      onOk: async () => {
        await logout();
        window.location.reload();
        onClose?.(e);
      },
    });
  };
  const avatar = userInfo?.avatar || userIcon;

  const onLoginRowClick = useCallback(() => {
    if (!hasLogin) {
      onLoginClick?.();
    } else {
      onGoToSetting?.();
      if (mobileStyle) {
        onNavClose?.();
      }
    }
  }, [hasLogin, mobileStyle, onGoToSetting, onLoginClick, onNavClose]);

  const onMemberRowClick = useCallback(() => {
    if (!hasLogin) {
      onLoginClick?.();
    } else {
      onPayModalOpen();
    }
  }, [hasLogin, onLoginClick, onPayModalOpen]);

  const onPayOk = useCallback( () => {
    refreshUserInfo();
  }, [refreshUserInfo]);

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
                {hasLogin ? userInfo?.name || t('user.defaultUserName') : t('user.notLogin')}
              </div>
            </div>
            <img className={styles.rowIcon} src={editIcon} alt="" />
          </div>
          <div className={styles.settingRow} onClick={onMemberRowClick}>
            <div>{t('navigation.memberSetting')}</div>
            <img className={styles.rowIcon} src={memberIcon} alt="" />
          </div>
          {hasLogin && (
            <div className={styles.settingRow} onClick={onLogoutClick}>
              <div>{t('user.logout')}</div>
              <img className={styles.rowIcon} src={exitLoginIcon} alt="" />
            </div>
          )}
        </div>
      </PopupModal>

      {payModalOpen &&
        (mobileStyle ? (
          <PayModalM
            open={payModalOpen}
            onCancel={onPayModalClose}
            onOk={onPayOk}
          />
        ) : (
          <PayModal
            open={payModalOpen}
            onCancel={onPayModalClose}
            onOk={onPayOk}
          />
        ))}
    </>
  );
};

export default memo(SettingModal);
