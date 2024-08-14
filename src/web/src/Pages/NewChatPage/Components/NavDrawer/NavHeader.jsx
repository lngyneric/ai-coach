import styles from './NavHeader.module.scss';
import LogoSquare from 'Components/logo/LogoSquare.jsx';
import { productName } from 'constants/productConstants';
import classNames from 'classnames';
import { memo } from 'react';
import LogoWithText from 'Components/logo/LogoWithText.jsx';

export const NavHeader = ({
  showCollapseBtn = true,
  isCollapse = false,
  showCloseBtn = false,
  onToggle = (isCollapse) => {},
  onClose = () => {},
}) => {
  return (
    <div
      className={classNames(
        styles.navHeader,
        isCollapse ? styles.collapse : ''
      )}
    >
      <div className={styles.logoArea}>
        {!isCollapse && <LogoWithText direction="row" size={30} />}
      </div>

      {showCollapseBtn && (
        <div
          className={styles.actionBtn}
          onClick={() => onToggle?.({ isCollapse: !isCollapse })}
        >
          <img
            src={require('@Assets/newchat/light/icon16-expand.png')}
            alt="展开/折叠"
            className={classNames(styles.icon)}
          />
        </div>
      )}
      { isCollapse && (
        <LogoWithText direction="col" size={30} />
      )}
      {showCloseBtn && (
        <div className={styles.actionBtn} onClick={onClose}>
          X
        </div>
      )}
    </div>
  );
};

export default memo(NavHeader);
