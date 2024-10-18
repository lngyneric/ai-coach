import { useCallback } from 'react';
import styles from './BirthdaySettingModal.module.scss';
import SettingBaseModal from './SettingBaseModal.jsx';
import { DatePickerView } from 'antd-mobile';
import { useState, memo } from 'react';

export const BirthdaySettingModal = ({
  open,
  onClose,
  onOk = ({ birthday }) => {},
}) => {
  const [value, setValue] = useState(new Date());
  const onOkClick = () => {
    onOk({ birthday: value });
  };
  const now = new Date();
  const min = new Date();
  min.setFullYear(now.getFullYear() - 100);

  const _onChange = useCallback((val) => {
    setValue(val);
  }, []);

  return (
    <SettingBaseModal
      className={styles.SexSettingModal}
      open={open}
      onClose={onClose}
      onOk={onOkClick}
      closeOnMaskClick={true}
    >
      <DatePickerView
        defaultValue={new Date('2000-01-01')}
        onChange={_onChange}
        min={min}
        mouseWheel={true}
      />
    </SettingBaseModal>
  );
};

export default memo(BirthdaySettingModal);
