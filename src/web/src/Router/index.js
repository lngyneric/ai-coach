import NewChatPage from "../Pages/NewChatPage/NewChatPage.jsx";
import UserAgreementPage from "Pages/UserAgreementPage/UserAgreementPage.jsx";
import PrivacyPolicyPage from "Pages/PrivacyPolicyPage/PrivacyPolicyPage.jsx";
import IndexNavigate from "./IndexNavigate.jsx";

/**
 * @description 用于存放导航栏的需要权限的路由，同时 系统的导航菜单也是基于此路由表进行渲染的
 * @type {*}
 * */
const routes = [
  {
    path: "/",
    element: <IndexNavigate to='/newchat'></IndexNavigate>,
  },
  {
    path: '/useraggrement',
    element: <UserAgreementPage />
  },
  {
    path: '/privacypolicy',
    element: <PrivacyPolicyPage />
  },
  {
    path: '/newchat',
    element: <NewChatPage />
  },
  {
    path: '/newchat/:cid',
    element: <NewChatPage />
  }
];

export default routes;
