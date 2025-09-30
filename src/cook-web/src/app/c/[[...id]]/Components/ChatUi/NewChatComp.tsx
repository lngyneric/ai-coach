import './ForkChatUI/styles/index.scss';
import 'markdown-flow-ui/dist/markdown-flow-ui.css';
import styles from './ChatComponents.module.scss';
import { useContext, useRef, memo, useCallback } from 'react';
import { ContentRender } from 'markdown-flow-ui';
import { useTranslation } from 'react-i18next';
import { useShallow } from 'zustand/react/shallow';
import { cn } from '@/lib/utils';
import { AppContext } from '../AppContext';
import { useChatComponentsScroll } from './ChatComponents/useChatComponentsScroll';
import useAutoScroll from './useAutoScroll';
import { useTracking } from '@/c-common/hooks/useTracking';
import { useDisclosure } from '@/c-common/hooks/useDisclosure';
import { useEnvStore } from '@/c-store/envStore';
import { useUserStore } from '@/store';
import { toast } from '@/hooks/useToast';
import PayModal from '../Pay/PayModal';
import PayModalM from '../Pay/PayModalM';
import { PREVIEW_MODE } from '@/c-api/studyV2';
import InteractionBlock from './InteractionBlock';
import useChatLogicHook from './useChatLogicHook';

export const NewChatComponents = ({
  className,
  lessonUpdate,
  onGoChapter,
  chapterId,
  lessonId,
  onPurchased,
  chapterUpdate,
  updateSelectedLesson,
  preview_mode = PREVIEW_MODE.NORMAL,
}) => {
  const { trackEvent, trackTrailProgress } = useTracking();
  const { t } = useTranslation();
  const chatBoxBottomRef = useRef<HTMLDivElement | null>(null);
  const showOutputInProgressToast = useCallback(() => {
    toast({
      title: t('chat.outputInProgress'),
    });
  }, [t]);

  const { courseId: shifuBid } = useEnvStore.getState();
  const { refreshUserInfo } = useUserStore(
    useShallow(state => ({
      refreshUserInfo: state.refreshUserInfo,
    })),
  );
  const { mobileStyle } = useContext(AppContext);

  const chatRef = useRef<HTMLDivElement | null>(null);
  const { scrollToLesson } = useChatComponentsScroll({
    chatRef,
    containerStyle: styles.chatComponents,
    messages: [],
    appendMsg: () => {},
    deleteMsg: () => {},
  });
  const { scrollToBottom } = useAutoScroll(chatRef as any, {
    threshold: 120,
  });

  const {
    open: payModalOpen,
    onOpen: onPayModalOpen,
    onClose: onPayModalClose,
  } = useDisclosure();

  const onPayModalOk = () => {
    onPurchased?.();
    refreshUserInfo();
  };

  const { items, isLoading, onSend, onRefresh, onTypeFinished } =
    useChatLogicHook({
      shifuBid,
      outlineBid: lessonId,
      lessonId,
      chapterId,
      previewMode: preview_mode,
      trackEvent,
      chatBoxBottomRef,
      trackTrailProgress,
      lessonUpdate,
      chapterUpdate,
      updateSelectedLesson,
      scrollToLesson,
      scrollToBottom,
      showOutputInProgressToast,
      onPayModalOpen,
    });

  return (
    <div
      className={cn(
        styles.chatComponents,
        className,
        mobileStyle ? styles.mobile : '',
      )}
      ref={chatRef}
    >
      {isLoading ? (
        <></>
      ) : (
        items.map((item, idx) =>
          item.like_status ? (
            <InteractionBlock
              key={`${item.generated_block_bid}-interaction`}
              shifu_bid={shifuBid}
              generated_block_bid={item.generated_block_bid}
              like_status={item.like_status}
              readonly={item.readonly}
              onRefresh={onRefresh}
            />
          ) : (
            <div
              key={idx}
              className={cn(
                'content-render-theme',
                mobileStyle ? 'mobile' : '',
              )}
            >
              <ContentRender
                typingSpeed={60}
                enableTypewriter={!item.isHistory}
                content={item.content}
                customRenderBar={item.customRenderBar}
                defaultButtonText={item.defaultButtonText}
                defaultInputText={item.defaultInputText}
                readonly={item.readonly}
                onSend={onSend}
                onTypeFinished={onTypeFinished}
              />
            </div>
          ),
        )
      )}
      <div
        ref={chatBoxBottomRef}
        id='chat-box-bottom'
      ></div>
      {payModalOpen &&
        (mobileStyle ? (
          <PayModalM
            open={payModalOpen}
            onCancel={onPayModalClose}
            onOk={onPayModalOk}
            type={''}
            payload={{}}
          />
        ) : (
          <PayModal
            open={payModalOpen}
            onCancel={onPayModalClose}
            onOk={onPayModalOk}
            type={''}
            payload={{}}
          />
        ))}
    </div>
  );
};

NewChatComponents.displayName = 'NewChatComponents';

export default memo(NewChatComponents);
