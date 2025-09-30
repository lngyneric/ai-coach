import styles from './ShortcutModal.module.scss';
import { memo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import clsx from 'clsx';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
import { useTranslation } from 'react-i18next';
import { useUiLayoutStore } from '@/c-store/useUiLayoutStore';

type Props = { open: boolean; onClose: () => void };
const ShortcutModal = ({ open, onClose }: Props) => {
  const { t } = useTranslation();
  const { inMacOs } = useUiLayoutStore(
    useShallow(state => ({ inMacOs: state.inMacOs })),
  );
  const shortcutKeysOptions: {
    id: string;
    titleKey: string;
    keys: string[];
  }[] = [
    {
      id: 'continue',
      titleKey: 'shortcut.continue',
      keys: [t('shortcut.keys.space')],
    },
    {
      id: 'ask',
      titleKey: 'shortcut.ask',
      keys: inMacOs
        ? [t('shortcut.keys.cmd'), t('shortcut.keys.shift'), 'A']
        : [t('shortcut.keys.ctrl'), t('shortcut.keys.shift'), 'A'],
    },
    {
      id: 'shortcut',
      titleKey: 'shortcut.showHelp',
      keys: inMacOs
        ? [t('shortcut.keys.cmd'), '/']
        : [t('shortcut.keys.ctrl'), '/'],
    },
  ];

  const getShortcutKey = (keyText: string, index: number) => {
    const isSingleText = keyText.length === 1;

    return (
      <div
        key={index}
        className={clsx(
          styles.shortcutKey,
          isSingleText ? styles.singleText : styles.multiText,
        )}
      >
        {keyText}
      </div>
    );
  };

  return (
    <Dialog
      open={open}
      onOpenChange={open => {
        if (!open) {
          onClose();
        }
      }}
    >
      <DialogContent className={styles.shortcutModal}>
        <DialogHeader>
          <DialogTitle className={styles.shortcutTitle}>
            {t('shortcut.title')}
          </DialogTitle>
        </DialogHeader>
        <div className={styles.shortcutContent}>
          {shortcutKeysOptions.map(option => {
            return (
              <div
                className={styles.shortcutRow}
                key={option.id}
              >
                <div className={styles.rowTitle}>{option.title}</div>
                <div className={styles.rowKeys}>
                  {option.keys.map((v, i) => {
                    return getShortcutKey(v, i);
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default memo(ShortcutModal);
