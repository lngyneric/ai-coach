import { useEffect } from "react";
import classNames from "classnames";
import NavDrawer from "./Components/NavDrawer/NavDrawer.jsx";
import ChatUi from "./Components/ChatUi/ChatUi.jsx";
import styles from "./NewChatPage.module.scss";
import { calcFrameLayout } from "@constants/uiContants.js";
import { useUiLayoutStore } from "@stores/useUiLayoutStore.js";
import { AppContext } from "@Components/AppContext.js";

// 课程学习主页面
const NewChatPage = (props) => {
  const { frameLayout, updateFrameLayout } = useUiLayoutStore((state) => state);

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
      <AppContext.Provider value={{frameLayout, isLogin: true, userInfo: null, theme: ''}}>
        <NavDrawer />
        <ChatUi />
      </AppContext.Provider>
    </div>
  );
};

export default NewChatPage;
