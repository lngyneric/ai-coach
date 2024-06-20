import { Modal } from 'antd';
import { useContext } from 'react';
import { AppContext } from 'Components/AppContext.js';

export const SettingModal = ({ open, children, onOKClick, onClose, defaultWidth='360px' }) => {
  const { isMobile } = useContext(AppContext);
  return (
    <Modal open={open} onOk={onOKClick} onCancel={onClose} >
      {children}
    </Modal>
  );
};
