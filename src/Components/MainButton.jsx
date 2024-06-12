import { Button } from "antd";
import styles from "./MainButton.module.scss";

export const MainButton = ({ disabled, children, width, height = 40, style, onClick }) => {
  return (
    <Button
      type="primary"
      shape="round"
      disabled={disabled}
      className={styles.mainButton}
      style={{ width, height, ...style }}
      onClick={onClick}
    >
      {children}
    </Button>
  );
};

export default MainButton;
