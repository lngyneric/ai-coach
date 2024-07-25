import Cookies from "js-cookie";
import routes from "./Router/index";
import { useRoutes } from "react-router-dom";
import { ConfigProvider } from "antd";
import locale from "antd/locale/zh_CN";

const RouterView = () => useRoutes(routes);

const App = () => {
  return (
    <ConfigProvider locale={locale}>
      <RouterView></RouterView>
    </ConfigProvider>
  );
};

export default App;
