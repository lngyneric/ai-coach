import { Button } from "antd";
import styles from "./MainButton.module.scss";
import classNames from "classnames";

export const MainButton = ({ disabled, children, width, height = 40, style, onClick, className }) => {
  return (
    <Button
      type="primary"
      shape="round"
      disabled={disabled}
      className={classNames(styles.mainButton, className)}
      style={{ width, height, ...style }}
      onClick={onClick}
    >
      {children}
    </Button>
  );
};

export default MainButton;
