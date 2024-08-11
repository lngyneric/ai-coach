import { Button, Modal, Select } from 'antd';
import { useCallback } from 'react';
import { memo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './PayModal.module.scss';
import { useDisclosture } from 'common/hooks/useDisclosture.js';
import CouponCodeModal from './CouponCodeModal.jsx';
import { QRCode } from 'antd';
import {
  ORDER_STATUS,
  PAY_CHANNEL_WECHAT,
  getPayChannelOptions,
} from './constans.js';
import { getPayUrl, initOrder, queryOrder } from 'Api/order.js';
import { useEffect } from 'react';
import classNames from 'classnames';
import { useInterval } from 'react-use';
import { useRef } from 'react';

const DEFAULT_QRCODE = 'DEFAULT_QRCODE';
const MAX_TIMEOUT = 1000 * 60 * 0.2;
const COUNTDOWN_INTERVAL = 1000;

export const PayModal = ({ open = false, onCancel, onOk }) => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [isTimeout, setIsTimeout] = useState(false);

  const [price, setPrice] = useState('');
  const [qrUrl, setQrUrl] = useState(DEFAULT_QRCODE);
  const [payChannel, setPayChannel] = useState(PAY_CHANNEL_WECHAT);
  const [interval, setInterval] = useState(null);
  const [orderId, setOrderId] = useState('');

  const timeoutRef = useRef();

  useInterval(async () => {
    if (timeoutRef.current <= 0) {
      setIsTimeout(true);
      setInterval(null);
    }
    timeoutRef.current = timeoutRef.current - COUNTDOWN_INTERVAL;

    const { data: resp } = await queryOrder({ orderId });

    if (resp.status === ORDER_STATUS.BUY_STATUS_SUCCESS) {
      setInterval(null);
      onOk?.();
    }
  }, interval);

  const onQrcodeRefresh = useCallback(() => {
    loadPayInfo();
  });

  const loadPayInfo = useCallback(async () => {
    setIsLoading(true);
    setIsTimeout(false)
    setQrUrl(DEFAULT_QRCODE);
    setPrice('0');
    setOrderId('');
    setInterval(null);

    const { data: resp } = await initOrder();
    if (resp.status !== ORDER_STATUS.BUY_STATUS_INIT) {
      return;
    }

    setPrice(resp.price);

    const orderId = resp.order_id;
    const { data: qrcodeResp } = await getPayUrl({
      channel: payChannel,
      orderId: orderId,
    });

    setQrUrl(qrcodeResp.qr_url);
    setOrderId(orderId);
    timeoutRef.current = MAX_TIMEOUT;
    setInterval(COUNTDOWN_INTERVAL);
    setIsLoading(false);
  }, [payChannel]);

  const getQrcodeStatus = useCallback(() => {
    if (isLoading) {
      return 'loading';
    }

    if (isTimeout) {
      return 'expired';
    }

    return 'active';
  }, [isLoading, isTimeout]);

  useEffect(() => {
    if (!open) {
      return;
    }
    loadPayInfo();
  }, [loadPayInfo, open]);

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

  const onPayChannelSelectChange = useCallback((e) => {
    setPayChannel(e);
  }, []);

  return (
    <>
      <Modal
        title={t('pay.payModalTitle')}
        open={open}
        footer={null}
        onCancel={_onCancel}
        className={styles.payModal}
        width={'800px'}
        closable={false}
      >
        <div className={styles.payModalContent}>
          <div className={styles.introSection}></div>
          <div className={styles.paySection}>
            <div className={styles.payInfoTitle}>扫码支付</div>
            <div className={styles.payChannelWrapper}>
              <span>支付方式：</span>
              <Select
                className={styles.payChannelSelect}
                options={getPayChannelOptions()}
                value={payChannel}
                style={{ width: '120px' }}
                onChange={onPayChannelSelectChange}
              />
            </div>
            <div className={styles.qrcodeWrapper}>
              <QRCode size={200} value={qrUrl} status={getQrcodeStatus()} onRefresh={onQrcodeRefresh} />
            </div>
            <div className={styles.priceWrapper}>
              <div
                className={classNames(
                  styles.price,
                  (isLoading || isTimeout) && styles.disabled
                )}
              >
                ￥ {price}
              </div>
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
