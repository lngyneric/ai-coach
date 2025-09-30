import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ComponentType,
  type RefObject,
} from 'react';
import { genUuid } from '@/c-utils/common';
import { fixMarkdownStream } from '@/c-utils/markdownUtils';
import { useCourseStore } from '@/c-store/useCourseStore';
import { useUserStore } from '@/store';
import { useShallow } from 'zustand/react/shallow';
import {
  StudyRecordItem,
  LikeStatus,
  getRunMessage,
  SSE_INPUT_TYPE,
  getLessonStudyRecord,
  PREVIEW_MODE,
  SSE_OUTPUT_TYPE,
  SYS_INTERACTION_TYPE,
  LIKE_STATUS,
} from '@/c-api/studyV2';
import { LESSON_STATUS_VALUE } from '@/c-constants/courseConstants';
import {
  events,
  EVENT_NAMES as BZ_EVENT_NAMES,
} from '@/app/c/[[...id]]/events';
import { EVENT_NAMES } from '@/c-common/hooks/useTracking';
import { OnSendContentParams } from 'markdown-flow-ui';
import LoadingBar from './LoadingBar';

export interface ChatContentItem {
  content: string;
  customRenderBar?: (() => JSX.Element | null) | ComponentType<any>;
  defaultButtonText: string;
  defaultInputText: string;
  readonly: boolean;
  isHistory?: boolean;
  generated_block_bid: string;
  like_status?: LikeStatus;
}

interface SSEParams {
  input: string | Record<string, any>;
  input_type: SSE_INPUT_TYPE;
  reload_generated_block_bid?: string;
}

export interface UseChatSessionParams {
  shifuBid: string;
  outlineBid: string;
  lessonId: string;
  chapterId?: string;
  previewMode?: (typeof PREVIEW_MODE)[keyof typeof PREVIEW_MODE];
  trackEvent: (name: string, payload?: Record<string, any>) => void;
  trackTrailProgress: (generatedBlockBid: string) => void;
  lessonUpdate?: (params: Record<string, any>) => void;
  chapterUpdate?: (params: Record<string, any>) => void;
  updateSelectedLesson: (lessonId: string) => void;
  scrollToLesson: (lessonId: string) => void;
  scrollToBottom: (behavior?: ScrollBehavior) => void;
  showOutputInProgressToast: () => void;
  onPayModalOpen: () => void;
  chatBoxBottomRef: React.RefObject<HTMLDivElement | null>;
}

export interface UseChatSessionResult {
  items: ChatContentItem[];
  isLoading: boolean;
  onSend: (content: OnSendContentParams) => void;
  onRefresh: (generatedBlockBid: string) => void;
  onTypeFinished: () => void;
}

/**
 * useChatLogicHook orchestrates the streaming chat lifecycle for lesson content.
 */
function useChatLogicHook({
  shifuBid,
  outlineBid,
  lessonId,
  chapterId,
  previewMode,
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
}: UseChatSessionParams): UseChatSessionResult {
  const { updateUserInfo } = useUserStore(
    useShallow(state => ({
      updateUserInfo: state.updateUserInfo,
    })),
  );
  const { updateResetedChapterId } = useCourseStore(
    useShallow(state => ({
      updateResetedChapterId: state.updateResetedChapterId,
    })),
  );

  const [contentList, setContentList] = useState<ChatContentItem[]>([]);
  const [isTypeFinished, setIsTypeFinished] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [lastInteractionBlock, setLastInteractionBlock] =
    useState<ChatContentItem | null>(null);
  const [loadedChapterId, setLoadedChapterId] = useState('');

  const contentListRef = useRef<ChatContentItem[]>([]);
  const currentContentRef = useRef<string>('');
  const currentBlockIdRef = useRef<string | null>(null);
  const runRef = useRef<((params: SSEParams) => void) | null>(null);
  const sseRef = useRef<EventSource | null>(null);

  const effectivePreviewMode = previewMode ?? PREVIEW_MODE.NORMAL;

  // first part of the content is loaded, scroll to the bottom
  useEffect(() => {
    if (contentList.length > 0) {
      setTimeout(() => {
        chatBoxBottomRef.current?.scrollIntoView();
        // there is a problem with the scrollToBottom, so we use the scrollIntoView instead
        // scrollToBottom("smooth");
      }, 100);
    }
  }, [contentList, scrollToBottom]);

  /**
   * Keeps the React state and mutable ref of the content list in sync.
   */
  const setTrackedContentList = useCallback(
    (
      updater:
        | ChatContentItem[]
        | ((prev: ChatContentItem[]) => ChatContentItem[]),
    ) => {
      setContentList(prev => {
        const next =
          typeof updater === 'function'
            ? (updater as (prev: ChatContentItem[]) => ChatContentItem[])(prev)
            : updater;
        contentListRef.current = next;
        return next;
      });
    },
    [],
  );

  /**
   * Applies stream-driven lesson status updates and triggers follow-up actions.
   */
  const lessonUpdateResp = useCallback(
    (response, isEnd: boolean) => {
      const {
        outline_bid: currentOutlineBid,
        status,
        title,
      } = response.content;
      lessonUpdate?.({
        id: currentOutlineBid,
        name: title,
        status,
        status_value: status,
      });
      if (status === LESSON_STATUS_VALUE.PREPARE_LEARNING && !isEnd) {
        runRef.current?.({
          input: '',
          input_type: SSE_INPUT_TYPE.NORMAL,
        });
      }

      if (status === LESSON_STATUS_VALUE.LEARNING && !isEnd) {
        updateSelectedLesson(currentOutlineBid);
      }
    },
    [lessonUpdate, updateSelectedLesson],
  );

  /**
   * Replaces provisional block ids with the server-specified identifiers.
   */
  const syncGeneratedBlockId = useCallback(
    (incomingId?: string | null) => {
      if (!incomingId) {
        return;
      }
      const previousId = currentBlockIdRef.current;
      if (!previousId || previousId === incomingId) {
        currentBlockIdRef.current = incomingId;
        return;
      }

      let changed = false;
      setTrackedContentList(prev => {
        const mapped = prev.map(item => {
          // if item has content , don't change the block id, because it's the content block or interaction block
          if (!item.content && item.generated_block_bid === previousId) {
            changed = true;
            return { ...item, generated_block_bid: incomingId };
          }
          return item;
        });
        return changed ? mapped : prev;
      });

      if (changed) {
        setLastInteractionBlock(prevState =>
          prevState && prevState.generated_block_bid === previousId
            ? { ...prevState, generated_block_bid: incomingId }
            : prevState,
        );
      }

      currentBlockIdRef.current = incomingId;
    },
    [setTrackedContentList],
  );

  /**
   * Starts the SSE request and streams content into the chat list.
   */
  const run = useCallback(
    (sseParams: SSEParams) => {
      sseRef.current?.close();
      setIsTypeFinished(false);

      const placeholderId = genUuid();
      currentBlockIdRef.current = placeholderId;
      currentContentRef.current = '';
      setLastInteractionBlock(null);
      setTrackedContentList(prev => {
        const placeholderItem: ChatContentItem = {
          generated_block_bid: placeholderId,
          content: '',
          customRenderBar: () => <LoadingBar />,
          defaultButtonText: '',
          defaultInputText: '',
          readonly: false,
        };

        return [...prev, placeholderItem];
      });

      let isEnd = false;

      const source = getRunMessage(
        shifuBid,
        outlineBid,
        effectivePreviewMode,
        sseParams,
        async response => {
          try {
            const nid = response.generated_block_bid;
            syncGeneratedBlockId(nid);
            const blockId = currentBlockIdRef.current;

            if (nid && [SSE_OUTPUT_TYPE.BREAK].includes(response.type)) {
              trackTrailProgress(nid);
            }

            if (response.type === SSE_OUTPUT_TYPE.INTERACTION) {
              setLastInteractionBlock({
                generated_block_bid: currentBlockIdRef.current || '',
                content: response.content,
                customRenderBar: () => null,
                defaultButtonText: '',
                defaultInputText: '',
                readonly: false,
              });
            } else if (response.type === SSE_OUTPUT_TYPE.CONTENT) {
              if (isEnd) {
                return;
              }

              const prevText = currentContentRef.current || '';
              const delta = fixMarkdownStream(prevText, response.content || '');
              const nextText = prevText + delta;
              currentContentRef.current = nextText;

              if (blockId) {
                setTrackedContentList(prevState => {
                  const updatedList = prevState.map(item =>
                    item.generated_block_bid === blockId
                      ? {
                          ...item,
                          content: nextText,
                          customRenderBar: () => null,
                        }
                      : item,
                  );
                  return updatedList;
                });
              }
            } else if (response.type === SSE_OUTPUT_TYPE.OUTLINE_ITEM_UPDATE) {
              if (response.content.have_children) {
                const { status, outline_bid: chapterBid } = response.content;
                chapterUpdate?.({
                  id: chapterBid,
                  status,
                  status_value: status,
                });
                if (status === LESSON_STATUS_VALUE.COMPLETED) {
                  isEnd = true;
                }
              } else {
                lessonUpdateResp(response, isEnd);
              }
            } else if (
              response.type === SSE_OUTPUT_TYPE.BREAK ||
              response.type === SSE_OUTPUT_TYPE.TEXT_END
            ) {
              if (blockId) {
                setTrackedContentList(prevState => {
                  const updatedList = prevState.map(item =>
                    item.generated_block_bid === blockId
                      ? { ...item, readonly: true, customRenderBar: () => null }
                      : item,
                  );
                  return updatedList;
                });
              }
              currentBlockIdRef.current = null;
              currentContentRef.current = '';
            } else if (response.type === SSE_OUTPUT_TYPE.PROFILE_UPDATE) {
              updateUserInfo({
                [response.content.key]: response.content.value,
              });
            }
          } catch (error) {
            console.warn('SSE handling error:', error);
          }
        },
      );
      sseRef.current = source;
    },
    [
      chapterUpdate,
      effectivePreviewMode,
      lessonUpdateResp,
      outlineBid,
      setTrackedContentList,
      shifuBid,
      syncGeneratedBlockId,
      trackTrailProgress,
      updateUserInfo,
    ],
  );

  useEffect(() => {
    return () => {
      sseRef.current?.close();
    };
  }, []);

  useEffect(() => {
    runRef.current = run;
  }, [run]);

  /**
   * Transforms persisted study records into chat-friendly content items.
   */
  const mapRecordsToContent = useCallback((records: StudyRecordItem[]) => {
    const result: ChatContentItem[] = [];
    records.forEach((item: StudyRecordItem) => {
      result.push({
        generated_block_bid: item.generated_block_bid,
        content: item.content,
        customRenderBar: () => null,
        defaultButtonText: item.user_input || '',
        defaultInputText: item.user_input || '',
        readonly: false,
        isHistory: true,
      });
      if (item.like_status) {
        result.push({
          generated_block_bid: item.generated_block_bid,
          content: '',
          like_status: item.like_status,
          customRenderBar: () => null,
          defaultButtonText: '',
          defaultInputText: '',
          readonly: false,
        });
      }
    });
    return result;
  }, []);

  /**
   * Loads the persisted lesson records and primes the chat stream.
   */
  const refreshData = useCallback(async () => {
    setTrackedContentList([]);
    setIsLoading(true);

    try {
      const recordResp = await getLessonStudyRecord({
        shifu_bid: shifuBid,
        outline_bid: outlineBid,
        preview_mode: effectivePreviewMode,
      });

      if (recordResp?.records?.length > 0) {
        const contentRecords = mapRecordsToContent(recordResp.records);
        setTrackedContentList(contentRecords);
        setIsTypeFinished(true);
        if (chapterId) {
          setLoadedChapterId(chapterId);
        }
        if (
          recordResp.records[recordResp.records.length - 1].block_type ===
          SSE_OUTPUT_TYPE.CONTENT
        ) {
          runRef.current?.({
            input: '',
            input_type: SSE_INPUT_TYPE.NORMAL,
          });
        }
      } else {
        runRef.current?.({
          input: '',
          input_type: SSE_INPUT_TYPE.NORMAL,
        });
      }
    } catch (error) {
      console.warn('refreshData error:', error);
    } finally {
      setIsLoading(false);
    }
  }, [
    chapterId,
    mapRecordsToContent,
    outlineBid,
    scrollToBottom,
    setTrackedContentList,
    shifuBid,
  ]);

  useEffect(() => {
    if (!chapterId) {
      return;
    }
    if (loadedChapterId === chapterId) {
      return;
    }
    setLoadedChapterId(chapterId);
  }, [chapterId, loadedChapterId]);

  useEffect(() => {
    const unsubscribe = useCourseStore.subscribe(
      state => state.resetedChapterId,
      curr => {
        if (!curr) {
          return;
        }

        if (curr === loadedChapterId) {
          refreshData();
          // @ts-expect-error resetedChapterId can be null per store design
          updateResetedChapterId(null);
        }
      },
    );

    return () => {
      unsubscribe();
    };
  }, [loadedChapterId, refreshData, updateResetedChapterId]);

  useEffect(() => {
    const unsubscribe = useUserStore.subscribe(
      state => state.isLoggedIn,
      isLoggedIn => {
        if (!isLoggedIn || !chapterId) {
          return;
        }
        setLoadedChapterId(chapterId);
        refreshData();
      },
    );

    return () => {
      unsubscribe();
    };
  }, [chapterId, refreshData]);

  useEffect(() => {
    if (!lessonId) {
      return;
    }
    refreshData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lessonId]);

  useEffect(() => {
    const onGoToNavigationNode = (
      event: CustomEvent<{ chapterId: string; lessonId: string }>,
    ) => {
      const { chapterId: targetChapterId, lessonId: targetLessonId } =
        event.detail;
      if (targetChapterId !== loadedChapterId) {
        return;
      }
      setIsTypeFinished(true);
      setLastInteractionBlock(null);
      scrollToLesson(targetLessonId);
      updateSelectedLesson(targetLessonId);
    };

    events.addEventListener(
      BZ_EVENT_NAMES.GO_TO_NAVIGATION_NODE,
      onGoToNavigationNode as EventListener,
    );

    return () => {
      events.removeEventListener(
        BZ_EVENT_NAMES.GO_TO_NAVIGATION_NODE,
        onGoToNavigationNode as EventListener,
      );
    };
  }, [loadedChapterId, scrollToLesson, updateSelectedLesson]);

  /**
   * updateContentListWithUserOperate rewinds the list to the chosen interaction point.
   */
  const updateContentListWithUserOperate = useCallback(
    (
      params: OnSendContentParams,
    ): { newList: ChatContentItem[]; needChangeItemIndex: number } => {
      const newList = [...contentListRef.current];
      const needChangeItemIndex = newList.findIndex(item =>
        item.content.includes(params.variableName || ''),
      );
      if (needChangeItemIndex !== -1) {
        newList[needChangeItemIndex] = {
          ...newList[needChangeItemIndex],
          readonly: false,
          defaultButtonText: params.buttonText || '',
          defaultInputText: params.inputText || '',
        };
        newList.length = needChangeItemIndex + 1;
        setTrackedContentList(newList);
      }

      return { newList, needChangeItemIndex };
    },
    [setTrackedContentList],
  );

  /**
   * onRefresh replays a block from the server using the original inputs.
   */
  const onRefresh = useCallback(
    (generatedBlockBid: string) => {
      if (!isTypeFinished) {
        showOutputInProgressToast();
        return;
      }

      const newList = [...contentListRef.current];
      const needChangeItemIndex = newList.findIndex(
        item => item.generated_block_bid === generatedBlockBid,
      );
      if (needChangeItemIndex === -1) {
        showOutputInProgressToast();
        return;
      }

      newList.length = needChangeItemIndex;
      setTrackedContentList(newList);

      setIsTypeFinished(false);
      runRef.current?.({
        input: '',
        input_type: SSE_INPUT_TYPE.NORMAL,
        reload_generated_block_bid: generatedBlockBid,
      });
    },
    [isTypeFinished, setTrackedContentList, showOutputInProgressToast],
  );

  /**
   * onSend processes user interactions and continues streaming responses.
   */
  const onSend = useCallback(
    (content: OnSendContentParams) => {
      if (!isTypeFinished) {
        showOutputInProgressToast();
        return;
      }

      const { variableName, buttonText, inputText } = content;
      if (buttonText === SYS_INTERACTION_TYPE.PAY) {
        trackEvent(EVENT_NAMES.POP_PAY, { from: 'show-btn' });
        onPayModalOpen();
        return;
      }
      if (buttonText === SYS_INTERACTION_TYPE.LOGIN) {
        if (typeof window !== 'undefined') {
          const redirect = encodeURIComponent(window.location.pathname);
          window.location.href = `/login?redirect=${redirect}`;
        }
        return;
      }

      const { newList, needChangeItemIndex } =
        updateContentListWithUserOperate(content);

      if (needChangeItemIndex === -1) {
        setTrackedContentList(newList);
      }

      setIsTypeFinished(false);
      // scrollToBottom();
      runRef.current?.({
        input: {
          [variableName as string]: buttonText || inputText,
        },
        input_type: SSE_INPUT_TYPE.NORMAL,
        reload_generated_block_bid:
          needChangeItemIndex !== -1
            ? newList[needChangeItemIndex].generated_block_bid
            : undefined,
      });
    },
    [
      isTypeFinished,
      onPayModalOpen,
      setTrackedContentList,
      showOutputInProgressToast,
      trackEvent,
      updateContentListWithUserOperate,
    ],
  );

  /**
   * onTypeFinished appends the interaction UI once streaming completes.
   */
  const onTypeFinished = useCallback(() => {
    if (lastInteractionBlock && contentList.length > 0) {
      const lastItem = contentList[contentList.length - 1];
      const gid = lastItem.generated_block_bid;
      const newInteractionBlock: ChatContentItem[] = [
        {
          generated_block_bid: gid,
          content: '',
          like_status: LIKE_STATUS.NONE,
          customRenderBar: () => null,
          defaultButtonText: '',
          defaultInputText: '',
          readonly: false,
        },
        lastInteractionBlock,
      ];
      setTrackedContentList(prev => [...prev, ...newInteractionBlock]);
      setLastInteractionBlock(null);
    }
    setIsTypeFinished(true);
  }, [contentList, lastInteractionBlock, setTrackedContentList]);

  const items = useMemo(
    () =>
      contentList.map(item => ({
        ...item,
        customRenderBar: item.customRenderBar || (() => null),
      })),
    [contentList],
  );

  return {
    items,
    isLoading,
    onSend,
    onRefresh,
    onTypeFinished,
  };
}

export default useChatLogicHook;
