import { memo, useCallback } from 'react';
import LineButton from 'Components/LineButton.jsx';
import classNames from 'classnames';
import { useCourseStore } from 'stores/useCourseStore.js';
import { Modal } from 'antd';

export const ResetChapterButton = ({ className, chapterId, onClick }) => {
  const { resetChapter } = useCourseStore((state) => ({
    resetChapter: state.resetChapter,
  }));

  const onButtonClick = useCallback(
    (e) => {
      Modal.confirm({
        title: '重置章节',
        content: '重置章节后，此章节的所有学习记录将清空，确定重置？',
        onOk: () => {
          resetChapter(chapterId);
        }
      });
      onClick?.(e);
    },
    [chapterId, onClick, resetChapter]
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
