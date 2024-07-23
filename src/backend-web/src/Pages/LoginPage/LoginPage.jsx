import React from "react";
import { Form, Input, Button, Checkbox } from "antd";
import { useForm } from "antd/es/form/Form";
import { useNavigate } from "react-router-dom";
import "./Loginpage.css";
import { Space, Row } from "antd";
import store from "store";
import { useEffect } from "react";
import { Link } from "react-router-dom";
import { login ,requireTmp} from "../../Api/user";
import { useState } from "react";
import { UploadEvent } from "../../Api/UploadEvent";
import ForgetPasswordModal from "./forgetPasswordModal/ForgetPasswordModal";
// Import Swiper React components
import { Swiper, SwiperSlide } from "swiper/react";
import { Autoplay, Navigation, Pagination } from "swiper/modules";
import "swiper/css";
import "swiper/css/navigation";
import "swiper/css/pagination";
import "swiper/css/autoplay";


const generateUUID = () => {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    var r = (Math.random() * 16) | 0,
      v = c == "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

const LoginForm = ({ handLogin }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const rememberInfo = store.get("accountInfo");
  const [form] = useForm();
  const [forgetPasswordModalProps, setForgetPasswordModalProps] = useState({
    open: false,
  });

  useEffect(() => {
    form.setFieldsValue(rememberInfo);
  });


  const tmpLogin = ()=>{
    setLoading(true)

    const uuid = generateUUID()
    requireTmp(uuid,'web').then((res)=>{
      console.log(res);
        store.set("userInfo", res.data.userInfo);
        store.set("token", res.data.token);
        UploadEvent("config", {
          user_unique_id: res.data.userInfo.user_id,
        });
        navigate("/"); 
    })
    .catch(() => {
      setLoading(false);
    });


  }

  const onFinish = ({ username, password, remember }) => {
    setLoading(true);
    if (remember === true) {
      store.set("accountInfo", { username, password, remember });
    } else {
      store.remove("accountInfo");
    }

    UploadEvent("login", {
      page: "login",
    });
    login(username, password)
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
        setLoading(false);
      });
  };

  const onForgetPwdButtonClick = () => {
    setForgetPasswordModalProps({
      open: true,
    });
  };

  const onForgetPwdCancel = () => {
    setForgetPasswordModalProps({
      open: false,
    });
  };

  const onForgetPwdOk = () => {
    setForgetPasswordModalProps({
      open: false,
    });
  };

  return (
    <div className="login_page">
      <div className="swiper_container">
        <Swiper
          modules={[Autoplay, Navigation, Pagination]}
          style={{ height: "100%" }}
          slidesPerView={1}
          onSlideChange={() => console.log("slide change")}
          onSwiper={(swiper) => console.log(swiper)}
          autoplay={{
            delay: 2000,
            stopOnLastSlide: false,
            disableOnInteraction: false,
          }}
          // navigation
          pagination={{
            clickable: true,
          }}
        >
          {/* <SwiperSlide>
            <div className="slider_container">
              <img
                src={require("../../Assets/logo-swiper/slider1.png")}
                alt=""
              />
              <div className="title">AI助手·你的智能工作/生活助手</div>
              <div className="title">你想要的，尽在AI助手</div>
              <div className="sub_title">
                日程安排｜待办事项｜文案撰写｜添加联系人｜收发邮件｜写代码｜外语翻译
              </div>
            </div>
          </SwiperSlide>
          <SwiperSlide>
            <div className="slider_container">
              <img
                src={require("../../Assets/logo-swiper/slider2.png")}
                alt=""
              />
              <div className="title">安排日程、记录待办</div>
              <div className="title">随时随地管理自己与协作的所有事情。</div>
              <div className="sub_title">
                支持手机、电脑多平台，语音和文字多种形式的输入，让你随时记录工作安排。
              </div>
            </div>
          </SwiperSlide>
          <SwiperSlide>
            <div className="slider_container">
              <img
                src={require("../../Assets/logo-swiper/slider3.png")}
                alt=""
              />
              <div className="title">写文案、写总结</div>
              <div className="title">各种文档随心写</div>
              <div className="sub_title">
                不管是商业文案还是营销方案，不论是新闻通稿还是计划总结……
                给出指令，AI助手可以帮你生成、改写、润色各种你想要的文档，写的东西又快又好。
              </div>
            </div>
          </SwiperSlide>
          <SwiperSlide>
            <div className="slider_container">
              <img
                src={require("../../Assets/logo-swiper/slider4.png")}
                alt=""
              />
              <div className="title">帮写代码</div>
              <div className="title">一句话省掉大半工作量</div>
              <div className="sub_title">
                代码生成 ｜代码解释 ｜代码纠错 ｜单元测试
              </div>
            </div>
          </SwiperSlide>
          <SwiperSlide>
            <div className="slider_container">
              <img
                src={require("../../Assets/logo-swiper/slider5.png")}
                alt=""
              />
              <div className="title">外语翻译</div>
              <div className="title">让你的业务遍布全球</div>
              <div className="sub_title">
                无论是论文、合同，还是邮件、文档，都能交给AI助手翻译，AI助手持包括英语、中文、法语、德语、西班牙语等129种语言，支持翻译完成直接发送对方邮箱，工作更轻松。
              </div>
            </div>
          </SwiperSlide> */}
        </Swiper>
      </div>

      <div className="login_container">
        <div className="login_header">
          <img
            className="logo"
            src={require("../../Assets/logo-03.png")}
            alt=""
          />
          <div className="title">AI 助手</div>
        </div>

        <div className="login-form_container">
          <div className="login-form_header">
            <div className="title">账号登录</div>
          </div>
          <Form
            name="normal_login"
            className="login_form"
            initialValues={{ remember: true }}
            onFinish={onFinish}
            form={form}
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: "请输入用户名!" }]}
            >
              <Input
                style={{ height: "52px" }}
                autoComplete="off"
                placeholder="用户名"
              />
            </Form.Item>
            <Form.Item
              name="password"
              rules={[{ required: true, message: "请输入密码!" }]}
            >
              <Input
                style={{ height: "52px" }}
                autoComplete="off"
                type="password"
                placeholder="密码"
              />
            </Form.Item>
            <Form.Item>
              <Row justify="space-between" align="middle">
                <Form.Item name="remember" valuePropName="checked" noStyle>
                  <Checkbox>记住我</Checkbox>
                </Form.Item>

                <Button type="link" onClick={onForgetPwdButtonClick}>
                  忘记密码？
                </Button>
              </Row>
            </Form.Item>

            <Form.Item>
              <Button
                style={{ height: "52px" }}
                type="primary"
                htmlType="submit"
                className="login-form-button"
                loading={loading}
              >
                登录
              </Button>
              <Button
                style={{ height: "52px" }}
                // type="primary"
                htmlType="submit"
                className="login-form-button"
                loading={loading}
                onClick={tmpLogin}
              >
                游客
              </Button>
            </Form.Item>
            <Form.Item>
              还没有账号？<Link to={{ pathname: "/register" }}>现在注册!</Link>
            </Form.Item>
          </Form>
          <ForgetPasswordModal
            open={forgetPasswordModalProps.open}
            cancel={onForgetPwdCancel}
            asyncOk={onForgetPwdOk}
          ></ForgetPasswordModal>
        </div>
        <div class="copyright wow animate__animated animate__fadeInUp">
          {/* <div>
            <a
              href="https://beian.miit.gov.cn/"
              target="_blank"
              rel="noreferrer"
            >
              
            </a>
            京ICP备2023005708号
            <a
              target="_blank"
              href="http://www.beian.gov.cn/portal/registerSystemInfo?recordcode="
              rel="noreferrer"
            >
              <img
                src={require("../../Assets/police-insignia.jpg")}
                style={{ height: "100%" }}
              />
              <span>京公网安备 </span>
            </a>
          </div> */}
          <div>版权所有©2024 瓜皮汤科技。保留所有权利。</div>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;
