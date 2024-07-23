import { Input } from "antd";
import { DatePicker } from "antd";
import { Select } from "antd";
import { Form, message } from "antd";
import { Modal } from "antd";
import { useForm } from "antd/es/form/Form";
import { useEffect, useState } from "react";
import { stateList } from "../Components/stateMap";
import { priorityList } from "../Components/PriorityMap";
import dayjs from "dayjs";
import { updateTodo } from "../../../Api/todo";

/**
 *
 *@description
 * @param {*} {open, state, onCancel, formData, onAsyncOk}
 * @return {*}
 */
const EditToDoModal = ({ open, state, onCancel, formData, onAsyncOk }) => {
  const stateTitleMap = {
    add: "添加待办",
    edit: "编辑待办",
  };

  const [confirmLoading, setConfirmLoading] = useState(false);
  const [form] = useForm();

  // 只在 数据发生变化时 调用 setFieldsValue 避免错误的 state 设置
  useEffect(() => {
    if (state === "add") {
      form.resetFields();
    }
    if (state === "edit") {
      // 深拷贝 formData
      const innerForm = JSON.parse(JSON.stringify(formData));
      innerForm.deadline = dayjs(new Date(innerForm.deadline));
      console.log(innerForm);
      form.setFieldsValue(innerForm);
    }
  }, [form, formData, state]);

  /**
   *@description 等待异步操作完成后在进行后续操作
   */
  const handleOk = () => {
    setConfirmLoading(true);

    updateTodo({
      todo_id: formData.todo_id,
      ...form.getFieldsValue(),
      deadline: form.getFieldValue("deadline").format("YYYY-MM-DD HH:mm:ss"),
    }).then((res) => {
      // message.success("操作成功");
      setConfirmLoading(false);
      onAsyncOk();
    });
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
          label="待办标题"
          name="title"
          rules={[{ required: true, message: "请输入待办标题" }]}
        >
          <Input placeholder="请输入待办标题"></Input>
        </Form.Item>
        {/* <Form.Item label="待办状态" name="state">
          <Select options={stateList} />
        </Form.Item> */}
        {/* <Form.Item label="优先级" name="priority">
          <Select options={priorityList} />
        </Form.Item> */}
        <Form.Item label="截止日期" name="deadline">
          <DatePicker format={"YYYY-MM-DD HH:mm:ss"}></DatePicker>
        </Form.Item>
        <Form.Item label="备注" name="description">
          <Input.TextArea></Input.TextArea>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default EditToDoModal;
