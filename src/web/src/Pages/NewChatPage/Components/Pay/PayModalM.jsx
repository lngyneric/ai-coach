import { memo, useState } from 'react';
import ModalM from 'Components/m/ModalM.jsx';
import styles from './PayModalM.module.scss';
import classNames from 'classnames';
import PayTotalDiscount from './PayTotalDiscount.jsx';

import weixinIcon from 'Assets/newchat/weixin.png';
import zhifuboIcon from 'Assets/newchat/zhifubao.png';

import RadioM from 'Components/m/RadioM.jsx';
import { Radio, Input } from 'antd-mobile';
import { PAY_CHANNEL_WECHAT_JSAPI, PAY_CHANNEL_ZHIFUBAO } from './constans.js';
import MainButtonM from 'Components/m/MainButtonM.jsx';
import payInfoBg from 'Assets/newchat/pay-info-bg-m.png';
import { useEffect } from 'react';

import { getPayUrl, initOrder, applyDiscountCode } from 'Api/order.js';
import { useWechat } from 'common/hooks/useWechat.js';
import { message } from 'antd';
import { inWechat } from 'constants/uiConstants.js';
import { useDisclosture } from 'common/hooks/useDisclosture.js';
import { useCallback } from 'react';
import { SettingInputM } from 'Components/m/SettingInputM.jsx';

export const PayModalM = ({ open = false, onCancel, onOk }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [price, setPrice] = useState('0.00');
  const [totalDiscount, setTotalDiscount] = useState('');
  const [payChannel, setPayChannel] = useState(
    inWechat() ? PAY_CHANNEL_WECHAT_JSAPI : PAY_CHANNEL_ZHIFUBAO
  );
  const [orderId, setOrderId] = useState('');
  const [couponCode, setCouponCode] = useState('');
  const { payByJsApi } = useWechat();
  const [messageApi, contextHolder] = message.useMessage();
  const {
    open: couponCodeModalOpen,
    onClose: onCouponCodeModalClose,
    onOpen: onCouponCodeModalOpen,
  } = useDisclosture();

  useEffect(() => {
    (async () => {
      const { data: resp } = await initOrder();
      setPrice(resp.value_to_pay);
      const orderId = resp.order_id;
      setOrderId(orderId);
      setTotalDiscount(resp.discount);
    })();
  }, []);

  const handlePay = useCallback(async () => {
    const { data: qrcodeResp } = await getPayUrl({
      channel: payChannel,
      orderId,
    });

    if (payChannel === PAY_CHANNEL_WECHAT_JSAPI) {
      try {
        await payByJsApi(qrcodeResp.qr_url);
        messageApi.success('支付成功');
        onOk();
      } catch (e) {
        messageApi.error('支付失败');
      }
    } else {
      window.open(qrcodeResp.qr_url);
    }
  }, [messageApi, onOk, orderId, payByJsApi, payChannel]);

  const onPayChannelChange = useCallback((value) => {
    setPayChannel(value);
  }, []);

  const onPayChannelWechatClick = useCallback(() => {
    setPayChannel(PAY_CHANNEL_WECHAT_JSAPI);
  }, []);

  const onPayChannelZhifubaoClick = useCallback(() => {
    setPayChannel(PAY_CHANNEL_ZHIFUBAO);
  }, []);

  const onCouponCodeButtonClick = useCallback(() => {
    onCouponCodeModalOpen();
  });

  const onCouponCodeOkClick = useCallback(async () => {
    const resp = await applyDiscountCode({ orderId, code: couponCode });
    if (resp.code !== 0) {
      messageApi.error(resp.message);
      return;
    }

    onOk();
  }, [couponCode, messageApi, onOk, orderId]);

  return (
    <>
      <ModalM
        className={''}
        visible={open}
        onClose={onCancel}
        style={{ wdith: '100%' }}
        content={
          <div className={styles.payModalContent}>
            <div className={styles.payInfoTitle}>首发特惠</div>
            <div className={styles.priceWrapper}>
              <div
                className={classNames(
                  styles.price,
                  isLoading && styles.disabled
                )}
              >
                <span className={styles.priceSign}>￥</span>
                <span className={styles.priceNumber}>{price}</span>
              </div>
            </div>
            <div className={styles.totalDiscountWrapper}>
              <PayTotalDiscount discount={totalDiscount} />
            </div>
            <div className={styles.payChannelWrapper}>
              <Radio.Group value={payChannel} onChange={onPayChannelChange}>
                {inWechat() && (
                  <div
                    className={classNames(
                      styles.payChannelRow,
                      payChannel === PAY_CHANNEL_WECHAT_JSAPI && styles.selected
                    )}
                    onClick={onPayChannelWechatClick}
                  >
                    <div className={styles.payChannelBasic}>
                      <img
                        src={weixinIcon}
                        alt="微信支付"
                        className={styles.payChannelIcon}
                      />
                      <span className={styles.payChannelTitle}>微信支付</span>
                    </div>
                    <RadioM
                      className={styles.payChannelRadio}
                      value={PAY_CHANNEL_WECHAT_JSAPI}
                    />
                  </div>
                )}
                <div
                  className={classNames(
                    styles.payChannelRow,
                    payChannel === PAY_CHANNEL_ZHIFUBAO && styles.selected
                  )}
                  onClick={onPayChannelZhifubaoClick}
                >
                  <div className={styles.payChannelBasic}>
                    <img
                      src={zhifuboIcon}
                      alt="支付宝支付"
                      className={styles.payChannelIcon}
                    />
                    <span className={styles.payChannelTitle}>支付宝支付</span>
                  </div>
                  <RadioM
                    className={styles.payChannelRadio}
                    value={PAY_CHANNEL_ZHIFUBAO}
                  />
                </div>
              </Radio.Group>
            </div>
            <div className={styles.buttonWrapper}>
              <MainButtonM className={styles.payButton} onClick={handlePay}>
                支付
              </MainButtonM>
            </div>
            <div className={styles.couponCodeWrapper}>
              <MainButtonM
                className={styles.couponCodeButton}
                fill="none"
                onClick={onCouponCodeButtonClick}
              >
                {'使用兑换码 >'}
              </MainButtonM>
            </div>
            <div className={styles.protocalWrapper}>
              <div className={styles.protocalDesc}>
                购买前请详细阅读以下协议内容
              </div>
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
            <div className={styles.payInfoWrapper}>
              <img className={styles.payInfo} src={payInfoBg} alt="产品说明" />
            </div>
          </div>
        }
      />
      {couponCodeModalOpen && (
        <ModalM
          visible={couponCodeModalOpen}
          title="兑换码"
          onClose={onCouponCodeModalClose}
          style={{ width: '80%' }}
          className={styles.couponCodeModal}
          content={
            <>
              <div className={styles.couponCodeInputWrapper}>
                <SettingInputM title="兑换码" onChange={(e) => setCouponCode(e)} />
              </div>
              <div class={styles.buttonWrapper}>
                <MainButtonM
                  onClick={onCouponCodeOkClick}
                  className={styles.okButton}
                >
                  确定
                </MainButtonM>
              </div>
            </>
          }
        />
      )}
      {contextHolder}
    </>
  );
};

export default memo(PayModalM);
