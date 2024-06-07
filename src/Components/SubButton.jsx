import { Button } from "antd";
import styles from "./SubButton.module.scss";

const SubButton = ({ disabled, children }) => {
  return (
    <Button shape="round" disabled={disabled}>
      {children}
    </Button>
  );
};

export default SubButton;
