import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import classNames from "classnames";
import styles from "./NewChatPage.module.scss";
import { Skeleton } from "antd";
import { calcFrameLayout } from "@constants/uiContants.js";
import { useUiLayoutStore } from "@stores/useUiLayoutStore.js";
import { useUserStore } from "@stores/useUserStore.js";
import { AppContext } from "@Components/AppContext.js";
import NavDrawer from "./Components/NavDrawer/NavDrawer.jsx";
import ChatUi from "./Components/ChatUi/ChatUi.jsx";
import LoginModal from "./Components/Login/LoginModal.jsx";
import { useLessonTree } from "./hooks/useLessonTree.js";
import { useCurrentLessonStore } from "@stores/useCurrentLessonStore";

// 课程学习主页面
const NewChatPage = (props) => {
  const { frameLayout, updateFrameLayout } = useUiLayoutStore((state) => state);
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const [firstLoading, setFirstLoading] = useState(true);
  const { hasLogin, userInfo, checkLogin } = useUserStore((state) => state);
  const {
    tree,
    loadTree,
    treeLoaded,
    setCurr,
    setCurrCatalog,
    toggleCollapse,
    catalogAvailable,
    getCurrElement,
    updateChapter,
  } = useLessonTree();
  const { cid } = useParams();
  const [currCatalogId, setCurrCatalogId] = useState(cid);
  const { lessonId, changeCurrLesson } = useCurrentLessonStore((state) => state);
  const navigate = useNavigate();

  // 判断布局类型
  useEffect(() => {
    const onResize = () => {
      const frameLayout = calcFrameLayout("#root");
      console.log("frame layout: ", frameLayout);
      updateFrameLayout(frameLayout);
    };
    window.addEventListener("resize", onResize);
    onResize();

    return () => {
      window.removeEventListener("resize", onResize);
    };
  }, []);

  const loadData = async () => {
    await loadTree();
  };

  useEffect(() => {
    (async () => {
      if (firstLoading) {
        await checkLogin();
      }
      await loadData();
      setFirstLoading(false);
    })();
  }, [hasLogin]);

  // 定位当前课程位置
  useEffect(() => {
    if (!tree || !treeLoaded) {
      return;
    }
    (async () => {
      if (cid) {
        if (!catalogAvailable(cid)) {
          navigate('/newchat');
        } else {
          setCurrCatalog(cid);
          const data = getCurrElement();
          if (data.lesson) {
            setCurr(data.lesson.id);
          }
        }
      } else {
        const data = getCurrElement();
        if (!data) {
          return;
        }
        if (data.lesson) {
          setCurr(data.lesson.id);
          changeCurrLesson(data.lesson.id);
          setCurrCatalogId(data.catalog.id);
        }
      }
    })();
  }, [treeLoaded, cid]);

  useEffect(() => {
    setCurr(lessonId); 
  }, [lessonId]);

  const onLoginModalClose = async () => {
    setLoginModalOpen(false);
    await loadData();
  };

  const onLessonUpdate = (val) => {
    updateChapter(val.id, val);
  }

  const onGoChapter = (id) => {
    navigate(`/newchat/${id}`);
  }

  return (
    <div className={classNames(styles.newChatPage)}>
      <AppContext.Provider
        value={{ frameLayout, hasLogin, userInfo, theme: "" }}
      >
        <Skeleton
          style={{ width: "100%", height: "100%" }}
          loading={firstLoading}
          paragraph={true}
          rows={10}
        >
          <NavDrawer
            onLoginClick={() => setLoginModalOpen(true)}
            lessonTree={tree}
            onLessonCollapse={toggleCollapse}
          />
          <ChatUi
            catalogId={currCatalogId}
            lessonUpdate={onLessonUpdate}
            onGoChapter={onGoChapter}
          />
        </Skeleton>
        {loginModalOpen && (
          <LoginModal
            open={loginModalOpen}
            onClose={onLoginModalClose}
            destroyOnClose={true}
          />
        )}
      </AppContext.Provider>
    </div>
  );
};

export default NewChatPage;
