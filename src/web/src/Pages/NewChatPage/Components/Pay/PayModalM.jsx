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

export const PayModalM = ({ open = false, onCancel, onOk }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [price, setPrice] = useState('');
  const [totalDiscount, setTotalDiscount] = useState('');

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
        </div>
      }
    />
  );
};

export default memo(PayModalM);
