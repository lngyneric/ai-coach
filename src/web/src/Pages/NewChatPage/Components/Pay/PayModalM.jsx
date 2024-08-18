import { memo, useState } from 'react';
import ModalM from 'Components/m/ModalM.jsx';
import styles from './PayModalM.module.scss';
import classNames from 'classnames';
import PayTotalDiscount from './PayTotalDiscount.jsx';

import weixinIcon from 'Assets/newchat/weixin.png';
import zhifuboIcon from 'Assets/newchat/zhifubao.png';

import RadioM from 'Components/m/RadioM.jsx';
import { Radio } from 'antd-mobile';
import { PAY_CHANNEL_WECHAT, PAY_CHANNEL_ZHIFUBAO } from './constans.js';
import MainButtonM from 'Components/m/MainButtonM.jsx';
import payInfoBg from 'Assets/newchat/pay-info-bg-m.png';
import { useEffect } from 'react';

import {
  getPayUrl,
  initOrder,
  queryOrder,
  applyDiscountCode,
} from 'Api/order.js';

export const PayModalM = ({ open = false, onCancel, onOk }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [price, setPrice] = useState('0.00');
  const [totalDiscount, setTotalDiscount] = useState('');
  const [payChannel, setPayChannel] = useState(PAY_CHANNEL_WECHAT);
  const [orderId, setOrderId] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);

  useEffect(() => {
    (async () => {
      const { data: resp } = await initOrder();
      setPrice(resp.value_to_pay);
      const orderId = resp.order_id;
      setOrderId(orderId);
    })()
  }, []);

  const handlePay = async () => {
    const { data: qrcodeResp } = await getPayUrl({
      channel: payChannel,
      orderId,
    });

    window.location.assign(qrcodeResp.qr_url);
  }

  return (
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
              className={classNames(styles.price, isLoading && styles.disabled)}
            >
              <span className={styles.priceSign}>￥</span>
              <span className={styles.priceNumber}>{price}</span>
            </div>
          </div>
          <div className={styles.totalDiscountWrapper}>
            <PayTotalDiscount discount={totalDiscount} />
          </div>
          <div className={styles.payChannelWrapper}>
            <Radio.Group>
              <div className={classNames(styles.payChannelRow, styles.selected) }>
                <div className={styles.payChannelBasic}>
                  <img
                    src={weixinIcon}
                    alt="微信支付"
                    className={styles.payChannelIcon}
                  />
                  <span className={styles.payChannelTitle}>微信支付</span>
                </div>
                <RadioM className={styles.payChannelRadio} value={PAY_CHANNEL_WECHAT} />
              </div>
              <div className={styles.payChannelRow}>
                <div className={styles.payChannelBasic}>
                  <img
                    src={zhifuboIcon}
                    alt="支付宝支付"
                    className={styles.payChannelIcon}
                  />
                  <span className={styles.payChannelTitle}>支付宝支付</span>
                </div>
                <RadioM className={styles.payChannelRadio} value={PAY_CHANNEL_ZHIFUBAO} />
              </div>
            </Radio.Group>
          </div>
          <div className={styles.buttonWrapper}>
            <MainButtonM className={styles.payButton} onClick={handlePay} >支付</MainButtonM>
          </div>
          <div className={styles.couponCodeWrapper}>
            <MainButtonM className={styles.couponCodeButton} fill='none' >{'使用兑换码 >'}</MainButtonM>
          </div>
          <div className={styles.protocalWrapper}>
            <div className={styles.protocalDesc}>购买前请详细阅读以下协议内容</div>
            <div className={styles.protocalLinks}>
              <a className={styles.protocalLink} href="/useraggrement" target='_blank' referrerPolicy='no-referrer' >《模型服务协议》</a>
              <a className={styles.protocalLink} href="/privacypolicy" target='_blank' referrerPolicy='no-referrer'>《用户隐私协议》</a>
            </div>
          </div>
          <div className={styles.payInfoWrapper}>
            <img className={styles.payInfo} src={payInfoBg} alt="产品说明" />
          </div>
        </div>
      }
    />
  );
};

export default memo(PayModalM);
