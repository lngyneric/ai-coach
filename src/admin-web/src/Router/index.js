import MainLayout from "../Layout/MainLayout";
import CommonListPage from "../Pages/CommonListPage/CommonListPage";
import SchedeleComponent from "../Pages/SchedulePage/SchedulePage";
import LoginPage from "../Pages/LoginPage/LoginPage";
import RegisterPage from "../Pages/RegisterPage/RegisterPage";
import ContactsComponant from "../Pages/ContactListPage/ContactListPage";
import { Navigate } from "react-router-dom";
import {
  ReadOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import SettingPage from "../Pages/SettingPage/SettingPage";
import BeforeEach from "./BeforeEach";
import NewChatPage from "../Pages/NewChatPage/NewChatPage.jsx";

/**
 * @description 用于存放导航栏的需要权限的路由，同时 系统的导航菜单也是基于此路由表进行渲染的
 * @type {*}
 * */
const authRoutes = [
  // {
  //   path: "/chat",
  //   element: <ChatPage></ChatPage>,
  //   title: "学习",
  //   icon: <ReadOutlined></ReadOutlined>,
  // },
  // {
  //   path: "/course",
  //   element: <ChatPage></ChatPage>,
  //   title: "课程",
  //   icon: <ReadOutlined></ReadOutlined>,
  // },
  {
    path: "/user",
    element: <ContactsComponant></ContactsComponant>,
    title: "用户",
  },
  {
    path: "/order",
    element: <CommonListPage></CommonListPage>,
  
    title: "订单",
  },
  {
    path: "/course",
    element: <ContactsComponant></ContactsComponant>,
    title: "课程",
  },
  {
    path: "/discount",
    element: <ContactsComponant></ContactsComponant>,
    title: "优惠",
  },
  {
    path: "/channel",
    element: <ContactsComponant></ContactsComponant>,
    title: "渠道",
  },
  {
    path: "/setting",
    element: <SettingPage></SettingPage>,
    title: "设置",
  },
];

const routes = [
  {
    path: "/",
    element: <Navigate to={authRoutes[0].path}></Navigate>,
  },
  {
    path: "/",
    element: (
      <BeforeEach authRoutes={authRoutes}>
        <MainLayout></MainLayout>
      </BeforeEach>
    ),
    children: authRoutes,
  },
  {
    path: "/login",
    element: <LoginPage></LoginPage>,
  },
  {
    path: "/register",
    element: <RegisterPage></RegisterPage>,
  },
  {
    path: '/newchat',
    element: <NewChatPage></NewChatPage>
  }
];
export { authRoutes };

export default routes;
