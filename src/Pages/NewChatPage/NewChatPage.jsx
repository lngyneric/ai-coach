import { useEffect, useState } from "react";
import classNames from "classnames";
import styles from "./NewChatPage.module.scss";
import { calcFrameLayout } from "@constants/uiContants.js";
import { useUiLayoutStore } from "@stores/useUiLayoutStore.js";
import { AppContext } from "@Components/AppContext.js";
import NavDrawer from "./Components/NavDrawer/NavDrawer.jsx";
import ChatUi from "./Components/ChatUi/ChatUi.jsx";
import LoginModal from './Components/Login/LoginModal.jsx';

// 课程学习主页面
const NewChatPage = (props) => {
  const { frameLayout, updateFrameLayout } = useUiLayoutStore((state) => state);
  const [loginModalOpen, setLoginModalOpen] = useState(false);

  // 判断布局类型
  useEffect(() => {
    const onResize = () => {
      const frameLayout = calcFrameLayout("#root");
      console.log("test fl ", frameLayout);
      updateFrameLayout(frameLayout);
    };
    window.addEventListener("resize", onResize);
    onResize();

    return () => {
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return (
    <div className={classNames(styles.newChatPage)}>
      <AppContext.Provider value={{frameLayout, isLogin: false, userInfo: null, theme: ''}}>
        <NavDrawer
          onLoginClick={() => { setLoginModalOpen(true)}}
        />
        <ChatUi />
        <LoginModal open={loginModalOpen} />
      </AppContext.Provider>
    </div>
  );
};

export default NewChatPage;
