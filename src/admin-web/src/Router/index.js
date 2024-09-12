import MainLayout from "../Layout/MainLayout";
import CommonListPage from "../Pages/CommonListPage/CommonListPage";
import LoginPage from "../Pages/LoginPage/LoginPage";
import RegisterPage from "../Pages/RegisterPage/RegisterPage";
import { Navigate } from "react-router-dom";
import SettingPage from "../Pages/SettingPage/SettingPage";
import BeforeEach from "./BeforeEach";
import NewChatPage from "../Pages/NewChatPage/NewChatPage.jsx";

/**
 * @description 用于存放导航栏的需要权限的路由，同时 系统的导航菜单也是基于此路由表进行渲染的
 * @type {*}
 * */
const authRoutes = [
  {
    path: "/userview",
    element: <CommonListPage viewName="userview"></CommonListPage>,
    title: "用户",
    showInMenu: true,
  },
  {
    path: "/feedback",
    element: <CommonListPage viewName="feedback"></CommonListPage>,
    title: "反馈",
    showInMenu: true,
  },
  {
    path: "/order",
    element: <CommonListPage viewName="order"></CommonListPage>,

    title: "订单",
    showInMenu: true,
  },
  {
    path: "/course",
    element:<CommonListPage viewName="courseview"></CommonListPage>,
    title: "课程",
    showInMenu: true,
  },

  {
    path: "/discount",
    element: <CommonListPage viewName="discount"></CommonListPage>,
    title: "优惠",
    showInMenu: true,
  },
  {
    path: "/setting",
    element: <SettingPage></SettingPage>,
    title: "设置",
    showInMenu: true,
  },
  {
    path: "/lessonview",
    element: <CommonListPage viewName="lessonview"></CommonListPage>,
    title: "课程",
    showInMenu: false,
  },
  {
    path: "/lessonscriptview",
    element: <CommonListPage viewName="lessonscriptview"></CommonListPage>,
    title: "脚本",
    showInMenu: false,
  },
  {
    path: "/attendlessonview",
    element: <CommonListPage viewName="attendlessonview"></CommonListPage>,
    title: "学习记录",
    showInMenu: false,
  },
  {
    path: "/logscriptview",
    element: <CommonListPage viewName="logscriptview"></CommonListPage>,
    title: "学习记录",
    showInMenu: false,
  },
  {
    path: "/:viewName",
    element: <CommonListPage></CommonListPage>,
    title: "列表",
    showInMenu: false,
  }
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
