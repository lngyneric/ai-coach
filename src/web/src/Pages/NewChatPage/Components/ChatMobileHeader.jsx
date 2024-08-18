import styles from './ChatMobileHeader.module.scss';
import IconButton from 'Components/IconButton.jsx';
import moeIcon from 'Assets/newchat/light/icon16-more2x.png';
import closeIcon from 'Assets/newchat/light/close-2x.png';
import classNames from 'classnames';
import { memo } from 'react';
import LogoWithText from 'Components/logo/LogoWithText.jsx';

export const ChatMobileHeader = (props) => {
  const { className, onSettingClick, navOpen } = props;

  return <div className={classNames(styles.ChatMobileHeader, className)}>
    <LogoWithText direction="row" size={30} />
    <IconButton icon={navOpen ? closeIcon : moeIcon} onClick={onSettingClick} />
  </div>
}

export default memo(ChatMobileHeader);
