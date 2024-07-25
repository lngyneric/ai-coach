import { Input } from "antd";
import { DatePicker } from "antd";
import { Select } from "antd";
import { Form } from "antd";
import { Modal } from "antd";
import { useForm } from "antd/es/form/Form";
import { useEffect, useState } from "react";

/**
 *
 *@description
 * @param {*} {open, state, onCancel, formData, onAsyncOk}
 * @return {*}
 */
const EditScheduleModal = ({ open, state, onCancel, formData, onAsyncOk }) => {
  const stateTitleMap = {
    add: "添加日程",
    edit: "编辑日程",
  };

  const [confirmLoading, setConfirmLoading] = useState(false);
  const [form] = useForm();

  // 只在 数据发生变化时 调用 setFieldsValue 避免错误的 state 设置
  useEffect(() => {
    if (state === "add") {
      form.resetFields();
    }
    if (state === "edit") {
      form.setFieldsValue(formData);
    }
  }, [form, formData, state]);

  /**
   *@description 等待异步操作完成后在进行后续操作
   */
  const handleOk = () => {
    setConfirmLoading(true);
    setTimeout(() => {
      setConfirmLoading(false);
      console.log(form.getFieldsValue());

      // 调用接口

      onAsyncOk();
    }, 2000);
  };

  return (
    <Modal
      forceRender
      open={open}
      title={stateTitleMap[state]}
      onCancel={onCancel}
      confirmLoading={confirmLoading}
      onOk={handleOk}
      okText="提交"
      cancelText="取消"
    >
      <Form form={form} labelCol={{ span: 4 }} wrapperCol={{ span: 20 }}>
        <Form.Item
          label="日程标题"
          name="name"
          rules={[{ required: true, message: "请输入日程标题" }]}
        >
          <Input placeholder="请输入日程标题"></Input>
        </Form.Item>
        <Form.Item label="开始时间" name="deadline">
          <DatePicker format={"YYYY-MM-DD"}></DatePicker>
        </Form.Item>
        <Form.Item label="截止时间" name="deadline">
          <DatePicker format={"YYYY-MM-DD"}></DatePicker>
        </Form.Item>
        <Form.Item label="地点" name="location">
          <Input placeholder="地点"></Input>
        </Form.Item>
        <Form.Item label="参与人" name="participants">
          <Input placeholder="参与人"></Input>
        </Form.Item>
        <Form.Item label="备注" name="remark">
          <Input.TextArea></Input.TextArea>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default EditScheduleModal;
