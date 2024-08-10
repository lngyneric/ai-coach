import styles from './NavBody.module.scss';
import LogoSquare from 'Components/logo/LogoSquare.jsx';
import { productName, slogan } from 'constants/productConstants';
import MainButton from 'Components/MainButton.jsx';
import { useTranslation } from 'react-i18next';
import { memo } from 'react';

export const NavBody = ({ 
  onLoginClick = () => {},
}) => {
  const { t } = useTranslation();
  return (<div className={styles.navBody}>
    <LogoSquare />
    <div className={styles.productName}>{productName}</div>
    <div className={styles.slogan}>{slogan}</div>
    <div className={styles.btnWrapper}>
      <MainButton width={185} onClick={() => onLoginClick?.()}>{t('user.loginMainButton')}</MainButton>
    </div>
  </div>)
}

export default memo(NavBody);
