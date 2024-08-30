import { Modal, Form, Input } from 'antd';
import MainButton from 'Components/MainButton.jsx';
import { calModalWidth } from 'Utils/common.js';
import styles from './FeedbackModal.module.scss';
import { memo } from 'react';
import { submitFeedback } from 'Api/user';
import { useState } from 'react';

const FEEDBACK_MAX_LENGTH = 300;

export const FeedbackModal = ({ open, onClose, inMobile = false }) => {
  const { TextArea } = Input;
  const [form] = Form.useForm();
  const [feedback, setFeedback] = useState('');

  const onSubmitFeedback = () => {
    console.log('submit feedback');
    console.log(form.values);
    form.validateFields().then((values) => {
      console.log(values);
      submitFeedback(values.feedback).then(() => {
        onClose();
        // message.success('提交成功');
      });
    });
  };

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
      <Form form={form} className={styles.formWrapper}>
        <Form.Item
          name="feedback"
        rules={[{ required: true, message: '请输入反馈内容' }]}>
          <TextArea
            value={feedback}
            showCount
            maxLength={FEEDBACK_MAX_LENGTH}
            minLength={5}
            style={{ height: '90px', resize: 'none' }}
          />
        </Form.Item>
      </Form>
      <MainButton className={styles.okBtn} width="100%" onClick={onSubmitFeedback}>
        提交
      </MainButton>
    </Modal>
  );
};

export default memo(FeedbackModal);
