import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import classNames from 'classnames';
import styles from './NewChatPage.module.scss';
import { Skeleton } from 'antd';
import { calcFrameLayout } from '@constants/uiContants.js';
import { useUiLayoutStore } from '@stores/useUiLayoutStore.js';
import { useUserStore } from '@stores/useUserStore.js';
import { AppContext } from '@Components/AppContext.js';
import NavDrawer from './Components/NavDrawer/NavDrawer.jsx';
import ChatUi from './Components/ChatUi/ChatUi.jsx';
import LoginModal from './Components/Login/LoginModal.jsx';
import { useLessonTree } from './hooks/useLessonTree.js';
import { useCourseStore } from '@stores/useCourseStore';
import Tu from './Tu.jsx';

// 课程学习主页面
const NewChatPage = (props) => {
  const { frameLayout, updateFrameLayout } = useUiLayoutStore((state) => state);
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const [firstLoading, setFirstLoading] = useState(true);
  const { hasLogin, userInfo, checkLogin } = useUserStore((state) => state);
  const [ensureLogin, setEnsureLogin] = useState(false);
  const {
    tree,
    loadTree,
    reloadTree,
    setCurr,
    setCurrCatalog,
    toggleCollapse,
    checkChapterAvaiableStatic,
    getCurrElementStatic,
    updateChapter,
  } = useLessonTree();
  const { cid } = useParams();
  const [ currChapterId, setCurrChapterId] = useState(null);
  const { lessonId, changeCurrLesson } = useCourseStore((state) => state);
  const navigate = useNavigate();

  // 判断布局类型
  useEffect(() => {
    const onResize = () => {
      const frameLayout = calcFrameLayout('#root');
      console.log('frame layout: ', frameLayout);
      updateFrameLayout(frameLayout);
    };
    window.addEventListener('resize', onResize);
    onResize();

    return () => {
      window.removeEventListener('resize', onResize);
    };
  }, []);

  const loadData = async () => {
    await loadTree();
  };

  useEffect(() => {
    (async () => {
      await checkLogin();
      setEnsureLogin(true);
    })();
  }, []);

  // 定位当前课程位置
  useEffect(() => {
    if (!ensureLogin) {
      return
    }
    (async () => {
      let nextTree;
      if (firstLoading || !tree) {
        nextTree = await loadTree();
      } else {
        nextTree = await reloadTree();
      }
      setFirstLoading(false);
      if (cid) {
        if (!checkChapterAvaiableStatic(nextTree, cid)) {
          navigate('/newchat');
        } else {
          setCurrChapterId(cid);
          const data = getCurrElementStatic(nextTree);

          if (data.lesson) {
            setCurr(data.lesson.id);
          }
        }
      } else {
        const data = getCurrElementStatic(nextTree);
        if (!data) {
          return;
        }

        if (data.catalog) {
          navigate(`/newchat/${data.catalog.id}`)
        }
      }
    })();
  }, [hasLogin, cid, ensureLogin]);

  useEffect(() => {
    setCurr(lessonId);
  }, [lessonId]);

  const onLoginModalClose = async () => {
    setLoginModalOpen(false);
    await loadData();
  };

  const onLessonUpdate = (val) => {
    updateChapter(val.id, val);
  };

  const onGoChapter = (id) => {
    navigate(`/newchat/${id}`);
  };

  const onPurchased = () => {
    reloadTree();
  }

  return (
    <div className={classNames(styles.newChatPage)}>
      <AppContext.Provider
        value={{ frameLayout, hasLogin, userInfo, theme: '' }}
      >
        <Skeleton
          style={{ width: '100%', height: '100%' }}
          loading={firstLoading}
          paragraph={true}
          rows={10}
        >
          <NavDrawer
            onLoginClick={() => setLoginModalOpen(true)}
            lessonTree={tree}
            onLessonCollapse={toggleCollapse}
          />
          {
            <ChatUi
              chapterId={currChapterId}
              lessonUpdate={onLessonUpdate}
              onGoChapter={onGoChapter}
              onPurchased={onPurchased}
            />
          }
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
