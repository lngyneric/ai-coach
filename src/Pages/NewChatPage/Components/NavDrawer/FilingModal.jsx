import PopupModal from '@Components/PopupModal';
import { Button } from 'antd';

import styles from './FilingModal.module.scss';

export const FillingModal = ({ open, onClose, style, onFeedbackClick }) => {
  return (
    <PopupModal open={open} onClose={onClose} wrapStyle={{ ...style}}>
      <div className={styles.filingModal}>
        <div>北京xxxx有限公司</div>
        <div>北京朝阳区望京xx大厦xx层xx02</div>
        <div><a className={styles.miitLink} href="https://beian.miit.gov.cn/" target="_blank" rel="noreferrer" >京ICP备2024060606</a></div>
        <div className={styles.gonganRow}>
          <img className={styles.beianIcon} src={require('@Assets/newchat/light/beian.png')} alt="备案" />
          <div>京公安网备gaxxxxxxxxxx</div>
        </div>
        <div className={styles.btnGroup}>
          <Button type="link" className={styles.actionBtn} onClick={onFeedbackClick}>提交反馈</Button>
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
