import { Button, Modal } from 'antd';
import { useCallback } from 'react';
import { memo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './PayModal.module.scss';
import { useDisclosture } from 'common/hooks/useDisclosture.js';
import CouponCodeModal from './CouponCodeModal.jsx';

export const PayModal = ({ open = false, onCancel, onOk }) => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [isTimeout, setIsTimeout] = useState(false);


  const {
    open: couponCodeModalOpen,
    onOpen: onCouponCodeModalOpen,
    onClose: onCouponCodeModalClose,
  } = useDisclosture();

  const _onCancel = useCallback(
    (e) => {
      onCancel?.(e);
    },
    [onCancel]
  );

  const onCouponCodeClick = useCallback(() => {
    onCouponCodeModalOpen();
  }, [onCouponCodeModalOpen]);

  const onCouponCodeOk = useCallback(async () => {
    // 调用接口

    // 关闭购买弹窗
    onOk?.();
  }, [onOk]);

  return (
    <>
      <Modal
        title={t('pay.payModalTitle')}
        open={true}
        footer={null}
        onCancel={_onCancel}
        className={styles.payModal}
      >
        <div className={styles.payModalContent}>
          <div className={styles.introSection}></div>
          <div className={styles.paySection}>
            <div className={styles.payInfoTitle}>微信扫码支付</div>
            <div className={styles.qrcodeWrapper}>
              <img src={''} alt="" />
            </div>
            <div className={styles.couponCodeWrapper}>
              <Button type="link" onClick={onCouponCodeClick}>
                使用优惠券
              </Button>
            </div>
          </div>
        </div>
      </Modal>
      <CouponCodeModal
        open={couponCodeModalOpen}
        onCancel={onCouponCodeModalClose}
        onOk={onCouponCodeOk}
      />
    </>
  );
};

export default memo(PayModal);
