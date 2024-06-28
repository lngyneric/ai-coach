import { useState } from 'react';
import styles from './BirthdaySettingModal.module.scss';
import SettingBaseModal from './SettingBaseModal.jsx';
import { DatePickerView } from 'antd-mobile';
import { useEffect } from 'react';

export const BirthdaySettingModal = ({
  open,
  onClose,
  onOk = ({ birthday }) => {},
  initialValues = {},
}) => {
  const [value, setValue] = useState(new Date());
  const [showPicker, setShowPicker] = useState(false);
  const onOkClick = () => {};
  const now = new Date();

  useEffect(() => {
    setTimeout(() => {
      setShowPicker(true);
    }, 2000);
  }, []);

  return (
    <SettingBaseModal
      className={styles.SexSettingModal}
      open={open}
      onClose={onClose}
      onOk={onOkClick}
    >
      {showPicker && (
        <DatePickerView
          defaultValue={now}
          onChange={(val) => {
            setValue(val);
          }}
        />
      )}
    </SettingBaseModal>
  );
};

export default BirthdaySettingModal;
