import classNames from 'classnames';
import { useState } from 'react';
import { Modal, Input, Button, Checkbox, Form, message } from 'antd';
import { useSendCode } from './useSendCode.js';
import styles from './LoginModal.module.scss';
import MainButton from '@Components/MainButton.jsx';
import { calModalWidth } from '@Utils/common.js';
import { genCheckCode, verifySmsCode } from '@Api/user.js';

const MODAL_STEP = {
  MOBILE: 1,
  CODE: 2,
  VERIFY_CODE: 3,
};

export const LoginModal = ({ open, width, onClose=() => {}, inMobile = false }) => {
  const [mobile, setMobile] = useState('');
  // const [countDown, setCountDown] = useState(0);
  const [mobileForm] = Form.useForm();
  const [codeForm] = Form.useForm();
  const [verifyCodeForm] = Form.useForm();
  const [modalStep, setModalStep] = useState(MODAL_STEP.MOBILE);
  const [countDown, sendCode, reset] = useSendCode({});
  const [aggrement, setAggrement] = useState(false);
  const [verifyCodeImage, setVerifyCodeImage] = useState('');
  const [messageApi, contextHolder] = message.useMessage();

  const updateVerifyCodeImage = async (mobile) => {
    const { data: res } = await genCheckCode(mobile);
    setVerifyCodeImage(res.img);
 }

  const onMobileFormOkClick = async () => {
    try {
      const { mobile } = await mobileForm.validateFields();
      setMobile(mobile);
      updateVerifyCodeImage(mobile);
      setModalStep(MODAL_STEP.VERIFY_CODE);
    } catch {}
  }

  const onVerifyCodeFormOkClick = async () => {
    try {
      const { checkCode } = await verifyCodeForm.validateFields();
      try {
        await sendCode(mobile, checkCode);
        setModalStep(MODAL_STEP.CODE);
      } catch (ex) {
        messageApi.error(ex.message);
      }
    } catch {}
  }

  const onCodeFromkOkClick = async () => {
    try {
      const { smsCode } = await codeForm.validateFields();
    } catch {}
  }

  const onLoginClick = async () => {
    if (modalStep === MODAL_STEP.MOBILE) {
      await onMobileFormOkClick();
    }

    if (modalStep === MODAL_STEP.CODE) {
      await onCodeFromkOkClick();
    }

    if (modalStep === MODAL_STEP.VERIFY_CODE) {
      await onVerifyCodeFormOkClick();
    }
  };

  return (
    <Modal
      open={open}
      footer={null}
      className={styles.loginModal}
      width={calModalWidth({ inMobile, width })}
      onCancel={onClose}
    >
      <div className={styles.title}>登录</div>
      <div className={styles.formWrapper}>
        {modalStep === MODAL_STEP.MOBILE && (
          <Form form={mobileForm} className={styles.mobileForm}>
            <Form.Item
              name="mobile"
              rules={[
                {
                  required: true,
                  message: "请输入11位手机号",
                  pattern: /^1\d{10}$/,
                },
              ]}
            >
              <Input
                className={classNames(styles.mobile, styles.sfInput)}
                placeholder="请输入手机号"
                maxLength={11}
                name="mobile"
              />
            </Form.Item>
          </Form>
        )}
        {modalStep === MODAL_STEP.CODE && (
          <Form form={codeForm} className={styles.codeForm}>
            <Form.Item
              name="smsCode"
              rules={[
                {
                  required: true,
                  message: "请输入4位验证码",
                  pattern: /^\d{4}$/,
                },
              ]}
            >
              <Input
                className={classNames(styles.smsCode, styles.sfInput)}
                maxLength={4}
                name="smsCode"
              />
            </Form.Item>
            <Button
              className={styles.sendBtn}
              disabled={countDown > 0}
              type="link"
              onClick={sendCode}
            >
              {countDown > 0 ? `重新发送(${countDown})` : "重新发送"}
            </Button>
          </Form>
        )}
        { modalStep === MODAL_STEP.VERIFY_CODE && (
          <Form
            className={styles.verifyCodeForm}
            form={verifyCodeForm}
          >
            <Form.Item 
              name="checkCode"
            >
              <Input
                className={classNames(styles.verifyCode, styles.sfInput)}
                maxLength={4}
                name="checkCode"
              />
            </Form.Item>
            <img className={styles.vcodeImage} src={verifyCodeImage} alt="图形验证码" onClick={() => {updateVerifyCodeImage(mobile)}} />
          </Form>
        )}
        <div
          className={styles.verifyCodeWrapper}
          style={{ display: "none" }}
        ></div>
      </div>
      <div className={styles.aggrementWrapper}>
        <div className={styles.aggrement}>
          <Checkbox className={styles.checkbox} onChange={(e) => setAggrement(e.target.checked)} />
          <div className={styles.text}>
            我已阅读并同意{" "}
            <a
              className={styles.link}
              href="x"
              target="_blank"
              rel="noreferrer"
            >
              服务协议 & 隐私政策
            </a>
          </div>
        </div>
        <div className={styles.feedback}>
          登录遇到问题？
          <a className={styles.link} href="x" target="_blank" rel="noreferrer">
            我要反馈
          </a>
        </div>
      </div>
      <div className={styles.btnWrapper}>
        <MainButton onClick={onLoginClick} width="100%">
          登录/注册
        </MainButton>
      </div>
      {contextHolder}
    </Modal>
  );
}

export default LoginModal;
