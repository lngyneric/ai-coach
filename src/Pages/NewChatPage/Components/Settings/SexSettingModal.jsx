import { useState } from 'react';
import styles from './SexSettingModal.module.scss';
import SettingBaseModal from './SettingBaseModal.jsx';
import classNames from 'classnames';


export const SexSettingModal = ({
  open,
  onClose,
  onOk = ({ sex }) => {},
  initialValues = {},
}) => {
  const [selectedSex, setSelectedSex] = useState(initialValues.sex);

  return <SettingBaseModal
    className={styles.SexSettingModal}
    open={open}
    onClose={onClose}
  >
    <div className={styles.sexWrapper}>
      <div className={classNames(styles.sexItem, selectedSex === 'male' ? 'selected' : '')} onClick={() => setSelectedSex('male')}>
        <img className={styles.itemIcon} src={require('@Assets/newchat/light/icon16-male@2x.png')} alt="male" />
        <div className={styles.itemTitle}>男性</div>
      </div>
      <div className={styles.sexItem} onClick={() => setSelectedSex('female')}>
        <img className={styles.itemIcon} src={require('@Assets/newchat/light/icon16-female@2x.png')} alt="female" />
        <div className={styles.itemTitle}>女性</div>
      </div>
      <div className={styles.sexItem} onClick={() => setSelectedSex('secret')}>
        <img className={styles.itemIcon} src={require('@Assets/newchat/light/icon16-account.png')} alt="secret" />
        <div className={styles.itemTitle}>保密</div>
      </div>
    </div>
  </SettingBaseModal>
};

export default SexSettingModal;
