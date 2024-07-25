import PopupModal from '@Components/PopupModal';
import { Button } from 'antd';

import styles from './FilingModal.module.scss';

export const FillingModal = ({ open, onClose, style }) => {
  return (
    <PopupModal open={open} onClose={onClose} wrapStyle={{ ...style}}>
      <div className={styles.filingModal}>
        <div>北京xxxx有限公司</div>
        <div>北京朝阳区望京xx大厦xx层xx02</div>
        <div>京ICP备2024060606</div>
        <div>京公安网备gaxxxxxxxxxx</div>
        <div className={styles.btnGroup}>
          <Button type="link" className={styles.actionBtn}>提交反馈</Button>
          <div>|</div>
          <Button type="link" className={styles.actionBtn}>服务协议</Button>
          <div>|</div>
          <Button type="link" className={styles.actionBtn}>隐私政策</Button>
        </div>
      </div>
    </PopupModal>
  );
}

export default FillingModal;
