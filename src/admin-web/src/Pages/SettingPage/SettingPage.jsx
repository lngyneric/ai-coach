import { Button, Input, Upload, Avatar, Row, Col } from "antd";
import { Space } from "antd";
import { Form } from "antd";
import { useForm } from "antd/es/form/Form";
import "./SettingPage.css";
import { Divider } from "antd";
import {
  AccountBookOutlined,
  CalendarOutlined,
  ContactsOutlined,
  EditOutlined,
  LockOutlined,
  PhoneOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Card } from "antd";
import { Modal } from "antd";
import FormModal from "./Modal/EditFormModal/FormModal";
import { useState } from "react";
import store from "store";

const accountInfo = store.get("userInfo") || { username: "", name: "" };
const SettingPage = () => {
  const [form] = useForm();
  const [formModalprops, setFormModalProps] = useState({
    formKey: "",
    open: false,
  });
  form.setFieldsValue(accountInfo);

  const onClickInfoCard = (formKey) => {
    setFormModalProps({ open: true, formKey });
  };

  const onOkFormModal = () => {
    setFormModalProps({ ...formModalprops, open: false });
  };

  const onCancelFormModal = () => {
    setFormModalProps({ ...formModalprops, open: false });
  };

  return (
    <div className="setting_page">
      <Space size="large">
        <Upload>
          {
            <Avatar
              style={{ fontSize: 28 }}
              size={64}
              icon={accountInfo.name ? accountInfo.namename : <UserOutlined />}
            >
              {accountInfo.name.substring(0, 1)}
            </Avatar>
          }
        </Upload>
        <Space.Compact direction="vertical" size="small">
          <div className="user-name">{accountInfo.name || "未设置用户名"}</div>
          <div className="user-email">{accountInfo.email}</div>
        </Space.Compact>
      </Space>
      <Divider></Divider>
      <Row gutter={16}>
        <Col span={8}>
          <Card
            className="info_card"
            hoverable={true}
            title="姓名"
            extra={
              <UserOutlined
                style={{ fontSize: 24, color: "#1677ff" }}
              ></UserOutlined>
            }
            onClick={() => {
              onClickInfoCard("editName");
            }}
          >
            <div>{accountInfo.name || "未设置用户名"}</div>
          </Card>
        </Col>
        <Col span={8}>
          <Card
            className="info_card"
            title="账号名称"
            extra={
              <ContactsOutlined
                style={{ fontSize: 24, color: "#1677ff" }}
              ></ContactsOutlined>
            }
          >
            <div>{accountInfo.username}</div>
          </Card>
        </Col>
        <Col span={8}>
          <Card
            className="info_card"
            title="手机号和电子邮件"
            extra={
              <PhoneOutlined
                style={{ fontSize: 24, color: "#1677ff" }}
              ></PhoneOutlined>
            }
          >
            <div>{accountInfo.email}</div>
            <div>{accountInfo.mobile}</div>
          </Card>
        </Col>
        <Col span={8}>
          <Card
            className="info_card"
            hoverable={true}
            title="密码"
            extra={
              <LockOutlined
                style={{ fontSize: 24, color: "#1677ff" }}
              ></LockOutlined>
            }
            onClick={() => {
              onClickInfoCard("password");
            }}
          >
            <div>更新您的密码保护您的账户安全</div>
          </Card>
        </Col>
      </Row>
      <FormModal
        open={formModalprops.open}
        formKey={formModalprops.formKey}
        onAsyncOk={onOkFormModal}
        onCancel={onCancelFormModal}
      ></FormModal>
    </div>
  );
};

export default SettingPage;
