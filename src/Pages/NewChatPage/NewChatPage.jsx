import { useEffect, useState } from "react";
import classNames from "classnames";
import styles from "./NewChatPage.module.scss";
import { Skeleton } from 'antd';
import { calcFrameLayout } from "@constants/uiContants.js";
import { useUiLayoutStore } from "@stores/useUiLayoutStore.js";
import { useUserStore } from '@stores/useUserStore.js';
import { AppContext } from "@Components/AppContext.js";
import NavDrawer from "./Components/NavDrawer/NavDrawer.jsx";
import ChatUi from "./Components/ChatUi/ChatUi.jsx";
import LoginModal from './Components/Login/LoginModal.jsx';

// 课程学习主页面
const NewChatPage = (props) => {
  const { frameLayout, updateFrameLayout } = useUiLayoutStore((state) => state);
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const [firstLoading, setFirstLoading] = useState(true);
  const { hasLogin, userInfo, checkLogin } = useUserStore((state) => state);

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

  const loadData = () => {
  };

  useEffect(() => {
    (async () => {
      await checkLogin();
      setFirstLoading(false);
    })()
  }, [])

  const onLoginModalClose = () => {
    setLoginModalOpen(false);
  }

  return (
    <div className={classNames(styles.newChatPage)}>
      <AppContext.Provider value={{frameLayout, hasLogin, userInfo, theme: ''}}>
          <Skeleton style={{ width: '100%', height: '100%' }} loading={firstLoading} paragraph={true} rows={10} >
            <NavDrawer
              onLoginClick={() => setLoginModalOpen(true)}
            />
            <ChatUi />
          </Skeleton>
        { loginModalOpen && <LoginModal open={loginModalOpen} onClose={onLoginModalClose} destroyOnClose={true} /> }
      </AppContext.Provider>
    </div>
  );
};

export default NewChatPage;
