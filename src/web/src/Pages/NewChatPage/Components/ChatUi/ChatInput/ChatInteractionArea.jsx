/**
 * 聊天输入区域
 * 目前有三种类型的输入，下一步，文本，按钮组
 */
import styles from './ChatInteractionArea.module.scss';
import ChatInputText from './ChatInputText.jsx';
import ChatButtonGroup from './ChatButtonGroup.jsx';
import ChatInputButton from './ChatInputButton.jsx';
import { useTranslation } from 'react-i18next';
import { Button } from 'antd';
import {
  INTERACTION_TYPE,
  INTERACTION_DISPLAY_TYPE,
} from 'constants/courseConstants.js';
import classNames from 'classnames';
import { memo, useRef, useEffect } from 'react';
import { useCallback } from 'react';
import React, { useState } from 'react'; // 添加 useState
import { Input } from 'antd-mobile';
import { ConfigProvider } from 'antd';

const INTERACTION_DISPLAY_MAP = {
  [INTERACTION_TYPE.CONTINUE]: INTERACTION_DISPLAY_TYPE.BUTTON,
  [INTERACTION_TYPE.INPUT]: INTERACTION_DISPLAY_TYPE.TEXT,
  [INTERACTION_TYPE.BUTTONS]: INTERACTION_DISPLAY_TYPE.BUTTONS,
  [INTERACTION_TYPE.NEXT_CHAPTER]: INTERACTION_DISPLAY_TYPE.BUTTON,
  [INTERACTION_TYPE.PHONE]: INTERACTION_DISPLAY_TYPE.TEXT,
  [INTERACTION_TYPE.CHECKCODE]: INTERACTION_DISPLAY_TYPE.TEXT,
  [INTERACTION_TYPE.ORDER]: INTERACTION_DISPLAY_TYPE.BUTTON,
  // [INTERACTION_TYPE.ASK]: INTERACTION_DISPLAY_TYPE.TEXT,
};

export const ChatInteractionArea = ({
  type = INTERACTION_DISPLAY_TYPE.TEXT,
  props = {},
  onSend = (type, val) => {},
  disabled = false,
  askMode = false,
  askVisible = true,
  askContent = "请输入追问内容",
  onSizeChange = ({ width, height }) => {},

}) => {
  const displayType = INTERACTION_DISPLAY_MAP[type];
  const elemRef = useRef();
  const {t} = useTranslation();
  const [isInputVisible, setInputVisible] = useState(false); // 添加状态

  const onSendFunc = (type, val) => {
    if (disabled) {
      return;
    }
    onSend?.(type, val, props.scriptId);
  };

  const genRenderControl = () => {
    switch (displayType) {
      case INTERACTION_DISPLAY_TYPE.BUTTON:
        return (
          <ChatInputButton
            disabled={disabled}
            type={type}
            props={props}
            onClick={onSendFunc}
          />
        );
      case INTERACTION_DISPLAY_TYPE.TEXT:
        return (
          <ChatInputText
            disabled={disabled}
            type={type}
            props={props}
            onClick={onSendFunc}
          />
        );
      case INTERACTION_DISPLAY_TYPE.BUTTONS:
        return (
          <ChatButtonGroup
            disabled={disabled}
            type={type}
            props={props}
            onClick={onSendFunc}
          />
        );
      default:
        return <></>;
    }
  };

  const resizeChange = useCallback((e) => {
    onSizeChange?.({
      width: e.contentRect.width,
      height: e.contentRect.height,
    });
  }, [onSizeChange]);
  const handleAskClick = () => {
    setInputVisible(!isInputVisible); // 显示输入框
  };

  const onSendAsk = (type, val) => {
    setInputVisible(false);
    onSendFunc?.(INTERACTION_TYPE.ASK, val);
  };

  useEffect(() => {
    // 监听的函数
    const resize = new ResizeObserver((e) => {
      if (!Array.isArray(e) || !e.length) return;
      for (const ent of e) {
        resizeChange(ent);
      }
    });
    // 传入监听对象
    resize.observe(elemRef?.current);
    // 及时销毁监听函数（重要!!!）
    const curr = elemRef?.current;
    return () => {
      resize.unobserve(curr);
    };
  }, [resizeChange]);


  return (
    <div
      className={classNames(styles.chatInputArea, disabled && styles.disabled)}
      ref={elemRef}
    >
      <div className={styles.controlContainer}>
        <div className={styles.controlWrapper}>
          {(!isInputVisible) && genRenderControl()} {/* 根据状态显示输入框 */}
          {isInputVisible && <ChatInputText id="askInput" onClick={onSendAsk} type="text" props = {t('chat.askContent')}  visible={isInputVisible}/>}

          <Button onClick={handleAskClick} className={styles.askButton} disabled={!askMode}>
            <div className={styles.askButtonContent}>
            <img src={require('@Assets/newchat/light/icon16-ask@1x.png')} alt=""  className={styles.askButtonIcon} />
            <span className={styles.askButtonText}>{t('chat.ask')}</span>
          </div>
        </Button>
        </div>
      </div>
      <div className={styles.tipText}>
        {t('chat.chatTips')}
      </div>
    </div>
  );
};

export default memo(ChatInteractionArea);
