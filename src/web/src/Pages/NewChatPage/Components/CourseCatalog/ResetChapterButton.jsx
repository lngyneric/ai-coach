import { memo, useCallback } from 'react';
import LineButton from 'Components/LineButton.jsx';
import classNames from 'classnames';
import { useCourseStore } from 'stores/useCourseStore.js';
import { Modal } from 'antd';
import { useTracking, EVENT_NAMES } from 'common/hooks/useTracking.js';

export const ResetChapterButton = ({ className, chapterId, chapterName, onClick, onConfirm }) => {
  const { trackEvent } = useTracking();
  const { resetChapter } = useCourseStore((state) => ({
    resetChapter: state.resetChapter,
  }));

  const onButtonClick = useCallback(
    (e) => {
      Modal.confirm({
        title: '确认重修',
        content: '重修会清空当前学习数据。确定重修？',
        onOk: () => {
          resetChapter(chapterId);
          trackEvent(EVENT_NAMES.RESET_CHAPTER_CONFIRM, {
            chapter_id: chapterId,
            chapter_name: chapterName,
          });
          onConfirm?.();
        }
      });
      trackEvent(EVENT_NAMES.RESET_CHAPTER, {
        chapter_id: chapterId,
        chapter_name: chapterName,
      });
      onClick?.(e);
    },
    [chapterId, chapterName, onClick, onConfirm, resetChapter, trackEvent]
  );

  return (
    <>
      <LineButton className={classNames(className)} onClick={onButtonClick} size="small" >
        重置
      </LineButton>
    </>
  );
};

export default memo(ResetChapterButton);
