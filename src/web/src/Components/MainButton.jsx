import { Button } from "antd";
import styles from "./MainButton.module.scss";
import classNames from "classnames";
import { ConfigProvider } from "antd";

export const MainButton = ({ disabled, children, width, height = 40, style, onClick, className }) => {
  return (
    <ConfigProvider
      theme={{
        components: {
          Button: {
            colorPrimary: '#042ED2',
            colorPrimaryHover: '#3658DB',
            colorPrimaryActive: '#0325A8',
            lineWidth: 0,
          },
        },
      }}
    >
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
    </ConfigProvider>
  );
};

export default MainButton;
