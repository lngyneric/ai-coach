import { Row, Button, Col, Input, Avatar } from "antd";
import { Form } from "antd";
import { Modal } from "antd";
import { useForm } from "antd/es/form/Form";
import { useEffect, useState } from "react";
import {
  MinusCircleOutlined,
  PlusOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Upload } from "antd";
import { updateContact } from "../../../Api/contact";

/**
 *
 *@description
 * @param {*} {open, state, onCancel, formData, onAsyncOk}
 * @return {*}
 */
const EditContactModal = ({ open, state, onCancel, formData, onAsyncOk }) => {
  const stateTitleMap = {
    add: "添加联系人",
    edit: "编辑联系人",
  };

  const [contactName, setContactName] = useState("");

  const [confirmLoading, setConfirmLoading] = useState(false);
  const [form] = useForm();

  // 只在 数据发生变化时 调用 setFieldsValue 避免错误的 state 设置
  useEffect(() => {
    setContactName(formData.name || "");
    if (state === "add") {
      form.resetFields();
      form.setFieldsValue({ phoneNumbers: [""], emails: [""] });
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
    updateContact({
      contact_id: formData.contact_id,
      ...form.getFieldsValue(),
    }).then(() => {
      setConfirmLoading(false);
      onAsyncOk();
    });
  };

  const onContactNameChange = ({ target }) => {
    console.log(target.value);
    setContactName(target.value);
  };

  return (
    <Modal
      width={620}
      open={open}
      title={stateTitleMap[state]}
      onCancel={onCancel}
      confirmLoading={confirmLoading}
      onOk={handleOk}
      okText="提交"
      cancelText="取消"
      forceRender={true}
    >
      <Form form={form} labelCol={{ span: 4 }} wrapperCol={{ span: 20 }}>
        <Form.Item wrapperCol={{ span: 24 }}>
          <Row justify="center">
            <Upload>
              {
                <Avatar
                  style={{ fontSize: 48 }}
                  size={120}
                  src={formData.avatar}
                  icon={contactName ? false : <UserOutlined />}
                >
                  {contactName.slice(0, 1)}
                </Avatar>
              }
            </Upload>
          </Row>
        </Form.Item>
        <Form.Item
          label="联系人姓名"
          name="name"
          rules={[{ required: true, message: "请输入联系人姓名" }]}
        >
          <Input
            placeholder="请输入联系人姓名"
            onChange={onContactNameChange}
          ></Input>
        </Form.Item>

        <Form.Item
          label="电话"
          name="mobile"
          rules={[{ required: true, message: "请输入联系人电话" }]}
        >
          <Input placeholder="请输入电话"></Input>
        </Form.Item>

        <Form.Item
          label="邮箱"
          name="email"
          rules={[{ required: true, message: "请输入联系人邮箱" }]}
        >
          <Input placeholder="请输入邮箱"></Input>
        </Form.Item>

        {/* <Form.List name="phoneNumbers">
          {(fields, { add, remove }) => (
            <>
              {fields.map((field) => (
                <Form.Item label="联系电话" {...field}>
                  <Row gutter={8} justify="space-between" align="middle">
                    <Col span={22}>
                      <Input placeholder="请输入联系电话" />
                    </Col>
                    <Col span={2}>
                      <MinusCircleOutlined onClick={() => remove(field.name)} />
                    </Col>
                  </Row>
                </Form.Item>
              ))}
              <Form.Item colon={false} label=" ">
                <Button
                  type="dashed"
                  icon={<PlusOutlined></PlusOutlined>}
                  onClick={() => {
                    add();
                  }}
                >
                  添加手机号
                </Button>
              </Form.Item>
            </>
          )}
        </Form.List>

        <Form.List name="emails">
          {(fields, { add, remove }) => (
            <>
              {fields.map((field) => (
                <Form.Item label="邮件地址" {...field}>
                  <Row gutter={8} justify="space-between" align="middle">
                    <Col span={22}>
                      <Input placeholder="请输入邮箱地址" />
                    </Col>
                    <Col span={2}>
                      <MinusCircleOutlined onClick={() => remove(field.name)} />
                    </Col>
                  </Row>
                </Form.Item>
              ))}
              <Form.Item colon={false} label=" ">
                <Button
                  type="dashed"
                  icon={<PlusOutlined></PlusOutlined>}
                  onClick={() => {
                    add();
                  }}
                >
                  添加邮件地址
                </Button>
              </Form.Item>
            </>
          )}
        </Form.List> */}

        {/* <Form.Item label="备注" name="remark">
          <Input.TextArea></Input.TextArea>
        </Form.Item> */}
      </Form>
    </Modal>
  );
};

export default EditContactModal;
