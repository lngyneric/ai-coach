import React from "react";
import { Form, Input, Button } from "antd";
import { useForm } from "antd/es/form/Form";
import { useNavigate, Link } from "react-router-dom";
import "./RegisterPage.css";
import { Space } from "antd";
import store from "store";
import { useEffect } from "react";
import { useState } from "react";
import { Modal } from "antd";
import { register } from "../../Api/admin";
import { UploadEvent } from "../../Api/UploadEvent";
import { login } from "../../Api/admin";

const RegisterPage = () => {
  const navigate = useNavigate();

  const rememberInfo = store.get("accountInfo");
  const [form] = useForm();
  useEffect(() => {
    form.setFieldsValue(rememberInfo);
  });

  let [verificationButtonText, setVerificationButtonText] =
    useState("获取验证码");
  let [verificationButtonDisabled, setVerificationButtonDisabled] =
    useState(false);
  let [registerloading, setRegisterLoading] = useState(false);

  const onFinish = (values) => {
    console.log(values);
    setRegisterLoading(true);
    UploadEvent("register", {
      page: "register",
    });

    register(values).then((res) => {
      console.log(res);
      setRegisterLoading(false);

      login(values.username, values.password)
        .then((res) => {
          console.log(res);
          store.set("userInfo", res.data.userInfo);
          store.set("token", res.data.token);
          UploadEvent("config", {
            user_unique_id: res.data.userInfo.user_id,
          });
          navigate("/");
        })
        .catch(() => {
          setRegisterLoading(false);
        });
    });
  };

  /**
   * @description 点击获取验证码的方法，倒计时
   */
  const onClickGetVerification = async () => {
    await form
      .validateFields(["email"])
      .then(() => {
        setVerificationButtonText("59s");
        verificationButtonText = 59;
        setVerificationButtonDisabled(true);
        const interval = setInterval(() => {
          if (verificationButtonText > 0) {
            verificationButtonText -= 1;
            setVerificationButtonText(`${verificationButtonText}s`);
          } else {
            clearInterval(interval);
            setVerificationButtonText("获取验证码");
            setVerificationButtonDisabled(false);
          }
        }, 1000);
      })
      .catch((err) => {
        console.log(err);
      });
  };

  const onClickCannotReceive = () => {
    Modal.info({
      title: "收不到验证码？",
      content: (
        <div>
          <p>建议检查邮箱垃圾箱，或更换其他邮箱重试</p>
        </div>
      ),
      okText: "好的",
    });
  };

  return (
    <div className="register_page">
      <Space direction="vertical" size="large">
        <div className="register-form_header">
          <div className="title">
            <img
              className="logo"
              src={require("../../Assets/logo-03.png")}
              alt=""
            />
            <div className="system-name">枕头后台管理系统</div>
          </div>

          <div className="slogan">Start here ~ 枕头后台管理系统! 🚀</div>
        </div>
        <Form
          name="normal_register"
          className="register_form"
          initialValues={{ remember: true }}
          onFinish={onFinish}
          form={form}
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: "请输入用户名!" }]}
          >
            <Input autoComplete="off" placeholder="用户名" />
          </Form.Item>
          <Form.Item
            name="mobile"
            rules={[{ required: true, message: "请输入手机号!" }]}
          >
            <Input autoComplete="off" placeholder="手机号" />
          </Form.Item>
          <Form.Item
            name="email"
            rules={[{ required: true, message: "请输入邮箱地址!" }]}
          >
            <Input autoComplete="off" placeholder="邮箱地址" />
          </Form.Item>

          {/* <Form.Item
                name="verification"
                rules={[{ required: true, message: '请输入验证码!' }]}>
                <div>
                    <Space.Compact
                        style={{width:"100%"}}>
                        <Input
                            placeholder='请输入验证码'>
                        </Input>
                        <Button
                            style={{width:"120px"}}
                            type='primary'
                            disabled={verificationButtonDisabled}
                            onClick={onClickGetVerification}>
                            {verificationButtonText}
                        </Button>
                    </Space.Compact>
                    <Button
                        type='link'
                        onClick={onClickCannotReceive}>
                        收不到验证码？
                    </Button>
                </div>
            </Form.Item> */}

          <Form.Item
            name="password"
            rules={[{ required: true, message: "请输入密码!" }]}
          >
            <Input autoComplete="off" type="password" placeholder="密码" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              className="register-form-button"
              loading={registerloading}
            >
              注册
            </Button>
            已经有账号了？ <Link to={{ pathname: "/login" }}>马上登录!</Link>
          </Form.Item>
        </Form>
      </Space>
    </div>
  );
};

export default RegisterPage;
