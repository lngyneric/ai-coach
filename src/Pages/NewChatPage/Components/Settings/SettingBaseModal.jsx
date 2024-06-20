import { Modal } from "antd";
import { calModalWidth } from "@Utils/common.js";
import { useUiLayoutStore } from "@stores/useUiLayoutStore.js";
import MainButton from "Components/MainButton.jsx";
import styles from './SettingBaseModal.module.scss';

export const SettingBaseModal = ({
  open,
  children,
  onOk,
  onClose,
  defaultWidth = "360px",
  header = <div className={styles.header}>设置</div>,
}) => {
  const { inMobile } = useUiLayoutStore((state) => state);

  return (
    <Modal
      open={open}
      onCancel={onClose}
      width={calModalWidth({ inMobile, width: defaultWidth })}
      className={styles.SettingBaseModal}
      footer={
        <div className={styles.btnWrapper}>
          <MainButton width="100%" onClick={onOk} >确定</MainButton>
        </div>
      }
    >
      {header}
      {children}
    </Modal>
  );
};

export default SettingBaseModal;
