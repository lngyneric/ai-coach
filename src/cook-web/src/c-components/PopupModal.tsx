import { useEffect, useRef } from 'react';

import clsx from 'clsx';
import styles from './PopupModal.module.scss';

import { useCallback } from 'react';

export const PopupModal = ({
  open = false,
  onClose,
  children,
  style,
  wrapStyle,
  className,
}) => {
  const popupRef = useRef(null);

  // Close the popup when clicking outside the modal
  const handleClickOutside = useCallback(
    event => {
      // @ts-expect-error EXPECT
      if (popupRef.current && !popupRef.current.contains(event.target)) {
        // `data-scroll-locked` indicates that another overlay is active, so the menu cannot be closed directly.
        // TODO: Migrate to `shadcn/ui`
        if (!document.body.getAttribute('data-scroll-locked')) {
          onClose?.(event);
        }
      }
    },
    [onClose],
  );

  // Listen for outside click events
  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [handleClickOutside]);

  return (
    <div
      className={clsx(styles.popupModalWrapper, className)}
      style={wrapStyle}
    >
      {open && (
        <div
          style={style}
          className={styles.popupModal}
          ref={popupRef}
        >
          {children}
        </div>
      )}
    </div>
  );
};

export default PopupModal;
