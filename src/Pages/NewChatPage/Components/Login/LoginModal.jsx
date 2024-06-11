import classNames from 'classnames';
import { useState } from 'react';
import { Modal, Input, Button, Checkbox, Form } from 'antd';
import styles from './LoginModal.module.scss';
import MainButton from '@Components/MainButton.jsx';

const MODAL_STEP = {
  MOBILE: 1,
  CODE: 2,
};

export const LoginModal = ({ open, width="360px" }) => {
  const [mobile, setMobile] = useState('');
  const [countDown, setCountDown] = useState(0);
  const [mobileForm] = Form.useForm();
  const [codeForm] = Form.useForm();
  const [modalStep, setModalStep] = useState(MODAL_STEP.MOBILE);

  const onLoginClick = async () => {
    try {
      const res = await mobileForm.validateFields();
      setMobile(res.mobile);
    } catch {}
  };

  return (<Modal open={open} footer={null} className={styles.loginModal} width={width}>
    <div className={styles.title}>登录</div>
    <div className={styles.formWrapper}>
      {
        modalStep === MODAL_STEP.MOBILE &&
        <Form
          form={mobileForm}
          className={styles.mobileForm}
        >
          <Form.Item
            name="mobile"
            rules={[{
              required: true,
              message: '请输入11位手机号',
              pattern: /^1\d{10}$/,
            }]}
          >
            <Input
              className={classNames(styles.mobile, styles.sfInput)}
              placeholder="请输入手机号"
              maxLength={11}
              name="mobile"
            />
          </Form.Item>
        </Form>
      }
      {
        modalStep === MODAL_STEP.CODE &&
        <Form
          form={codeForm}
        >
          <Form.Item
            name="code"
            rules={[{
              required: true,
              message: '请输入4位验证码',
              pattern: /^\d{4}$/,
            }]}
          >
            <Input className={classNames(styles.verifyCode, styles.sfInput) } maxLength={4} name="code" />
          </Form.Item>
          <Button className={styles.sendBtn} type="link">{countDown ? `重新发送(${countDown})`: '重新发送'}</Button>
        </Form>
      }
      <div className={styles.verifyCodeWrapper} style={{display: 'none'}}>
      </div>
    </div>
    <div className={styles.aggrementWrapper}>
      <div className={styles.aggrement}>
        <Checkbox className={styles.checkbox} />
        <div className={styles.text}>我已阅读并同意 <a className={styles.link} href="x" target="_blank" rel="noreferrer">服务协议 & 隐私政策</a></div>
      </div>
      <div className={styles.feedback}>
        登录遇到问题？<a className={styles.link} href="x" target="_blank" rel="noreferrer">我要反馈</a>
      </div>
    </div>
    <div className={styles.btnWrapper}>
      <MainButton onClick={onLoginClick} width="100%">登录/注册</MainButton>
    </div>
  </Modal>)
}

export default LoginModal;
