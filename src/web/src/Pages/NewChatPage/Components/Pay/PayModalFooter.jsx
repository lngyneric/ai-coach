import { memo } from 'react';
import styles from './PayModalFooter.module.scss';
import classNames from 'classnames';

export const PayModalFooter = ({ className }) => {
  return (
    <div className={classNames(styles.protocalWrapper, className)}>
      <div className={styles.protocalDesc}>购买前请详细阅读以下协议内容</div>
      <div className={styles.protocalLinks}>
        <a
          className={styles.protocalLink}
          href="/useraggrement"
          target="_blank"
          referrerPolicy="no-referrer"
        >
          《模型服务协议》
        </a>
        <a
          className={styles.protocalLink}
          href="/privacypolicy"
          target="_blank"
          referrerPolicy="no-referrer"
        >
          《用户隐私协议》
        </a>
      </div>
    </div>
  );
};

export default memo(PayModalFooter);
