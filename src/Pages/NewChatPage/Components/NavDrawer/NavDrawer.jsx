/*
 * 左侧导航控件容器
 */
import { AppContext } from "@Components/AppContext.js";
import { useContext, useState, useRef } from "react";

import NavHeader from "./NavHeader.jsx";
import NavBody from "./NavBody.jsx";
import NavFooter from "./NavFooter.jsx";
import FillingModal from "./FilingModal.jsx";
import ThemeWindow from "./ThemeWindow.jsx";
import SettingModal from "./SettingModal.jsx";
import CourseCatalogList from "../CourseCatalog/CourseCatalogList.jsx";
import styles from "./NavDrawer.module.scss";
import FeedbackModal from "../FeedbackModal/FeedbackModal.jsx";

import {
  FRAME_LAYOUT_PAD,
  FRAME_LAYOUT_PAD_INTENSIVE,
  FRAME_LAYOUT_MOBILE,
} from "@constants/uiConstants";

/**
 * 导航栏展示形式
 * 0: 默认，在 dom 流中展示
 * 1：作为抽屉展示
 */
export const NAV_SHOW_TYPE_NORMAL = 0;
export const NAV_SHOW_TYPE_DRAWER = 1;

/**
 * 小窗口状态
 */
export const POPUP_WINDOW_STATE_CLOSE = 0;
export const POPUP_WINDOW_STATE_THEME = 2;
export const POPUP_WINDOW_STATE_SETTING = 3;
export const POPUP_WINDOW_STATE_FILING = 1;

const calcNavWidth = (frameLayout) => {
  if (frameLayout === FRAME_LAYOUT_MOBILE) {
    return "100%";
  }
  if (frameLayout === FRAME_LAYOUT_PAD_INTENSIVE) {
    return "280px";
  }
  if (frameLayout === FRAME_LAYOUT_PAD) {
    return "25%";
  }
  return "280px";
};

const COLLAPSE_WIDTH = "60px";

const NavDrawer = ({
  showType = NAV_SHOW_TYPE_NORMAL,
  onLoginClick = () => {},
  lessonTree,
  onChapterCollapse = () => {},
  onLessonSelect = () => {},
}) => {
  const { frameLayout, hasLogin } = useContext(AppContext);
  const [isCollapse, setIsCollapse] = useState(false);
  const [popupModalState, setPopupModalState] = useState(
    POPUP_WINDOW_STATE_CLOSE
  );
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);

  const alwaysShowLessonTree = !!parseInt(process.env.REACT_APP_ALWAYS_SHOW_LESSON_TREE); 
  const footerRef = useRef(null);

  const onHeaderCloseClick = () => {
    console.log("onHeaderCloseClick");
  };

  const onHeaderToggleClick = ({ isCollapse }) => {
    setIsCollapse(isCollapse);
  };

  const onPopupModalClose = (e) => {
    if (footerRef.current && footerRef.current.containElement(e.target)) {
      return
    }
    setPopupModalState(POPUP_WINDOW_STATE_CLOSE);
  };

  const popupWindowStyle = {
    left: "50%",
    transform: "translate(-50%)",
    width: "250px",
    top: "auto",
    bottom: 80,
  };

  return (
    <div
      className={styles.navDrawerWrapper}
      style={{ width: isCollapse ? COLLAPSE_WIDTH : calcNavWidth(frameLayout) }}
    >
      <div className={styles.navDrawer}>
        <NavHeader
          onClose={onHeaderCloseClick}
          onToggle={onHeaderToggleClick}
          isCollapse={isCollapse}
        />
        <div className={styles.bodyWrapper}>
          {!isCollapse &&
            ((hasLogin || alwaysShowLessonTree) ? (
              <CourseCatalogList
                catalogs={lessonTree?.catalogs || []}
                catalogCount={lessonTree?.catalogCount || 0}
                lessonCount={lessonTree?.lessonCount || 0}
                onChapterCollapse={onChapterCollapse}
                onLessonSelect={onLessonSelect}
              />
            ) : (
              <NavBody onLoginClick={onLoginClick} />
            ))}
        </div>
        <NavFooter
          ref={footerRef}
          isCollapse={isCollapse}
          onFilingClick={() => {
            if (popupModalState === POPUP_WINDOW_STATE_FILING) {
              setPopupModalState(POPUP_WINDOW_STATE_CLOSE);
            } else {
              setPopupModalState(POPUP_WINDOW_STATE_FILING);
            }
          }}
          onThemeClick={() => {
            if (popupModalState === POPUP_WINDOW_STATE_THEME) {
              setPopupModalState(POPUP_WINDOW_STATE_CLOSE);
            } else {
              setPopupModalState(POPUP_WINDOW_STATE_THEME);
            }
          }}
          onSettingsClick={() => {
            if (popupModalState === POPUP_WINDOW_STATE_SETTING) {
              setPopupModalState(POPUP_WINDOW_STATE_CLOSE);
            } else {
              setPopupModalState(POPUP_WINDOW_STATE_SETTING);
            }
          }}
        />
        <FillingModal
          open={popupModalState === POPUP_WINDOW_STATE_FILING}
          style={popupWindowStyle}
          onClose={onPopupModalClose}
          onFeedbackClick={() => {
            setFeedbackModalOpen(true);
          }}
        />
        <ThemeWindow
          open={popupModalState === POPUP_WINDOW_STATE_THEME}
          style={popupWindowStyle}
          onClose={onPopupModalClose}
        />
        <SettingModal
          open={popupModalState === POPUP_WINDOW_STATE_SETTING}
          style={popupWindowStyle}
          onClose={onPopupModalClose}
          onLoginClick={onLoginClick}
        />
        <FeedbackModal
          open={feedbackModalOpen}
          onClose={() => {
            setFeedbackModalOpen(false);
          }}
        />
      </div>
    </div>
  );
};

export default NavDrawer;
