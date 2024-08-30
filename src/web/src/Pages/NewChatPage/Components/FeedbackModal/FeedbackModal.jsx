import { Modal, Form, Input, message } from 'antd';
import MainButton from 'Components/MainButton.jsx';
import { calModalWidth } from 'Utils/common.js';
import styles from './FeedbackModal.module.scss';
import { memo } from 'react';
import { useCallback } from 'react';
import { submitFeedback } from 'Api/bz.js';

const FEEDBACK_MAX_LENGTH = 300;

export const FeedbackModal = ({ open, onClose, inMobile = false }) => {
  const { TextArea } = Input;
  const [form] = Form.useForm();
  const [messageApi, contextHolder] = message.useMessage();

  const onSubmitFeedback = useCallback(async () => {
    try {
      const data = await form.validateFields();
      const { feedback } = data;
      await submitFeedback(feedback);
      messageApi.success({
        content: '反馈成功，感谢你的反馈。'
      });
      onClose();
    } catch {}
  }, [form, messageApi, onClose]);

  return (
    <Modal
      className={styles.feedbackModal}
      width={calModalWidth({ inMobile })}
      open={open}
      footer={null}
      maskClosable={true}
      onCancel={onClose}
    >
      <div className={styles.title}>反馈</div>
      <Form className={styles.formWrapper} form={form}>
        <Form.Item name="feedback" rules={[{ required: true, message: '请输入反馈内容' }]}>
          <TextArea
            name="feedback"
            showCount
            maxLength={FEEDBACK_MAX_LENGTH}
            style={{ height: '90px', resize: 'none' }}
          />
        </Form.Item>
      </Form>
      <MainButton className={styles.okBtn} width="100%" onClick={onSubmitFeedback}>
        提交
      </MainButton>
      { contextHolder }
    </Modal>
  );
};

export default memo(FeedbackModal);
