import { Layout } from "antd";
import { Outlet } from "react-router-dom";
import SiderNavMenu from "./Menu/SiderNavMenu";
import UserAvatar from "./Component/UserAvatar";
import store from "store";
import { UploadEvent } from "../Api/UploadEvent";
import HeaderNavMenu from "./Menu/HeaderNavMenu";
import { Divider } from "antd";
const MainLayout = () => {
  return (
    <Layout
      style={{
        height: "100%",
      }}
    >
      <Layout.Header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          backgroundColor: "#fff",
        }}
      >
        {/* <div className="logo">
         */}
        {/* <img
          style={{ width: 120, marginRight: 8, marginLeft: 24 }}
          src={require("../Assets/logo-fullname.png")}
        ></img> */}
        <div
          style={{
            fontSize: 18,
            marginRight: 42,
          }}
        >
         枕头后台管理系统
        </div>
        <Divider
          type="vertical"
          style={{ height: 38, borderWidth: 2 }}
        ></Divider>
        {/* </div> */}
        <HeaderNavMenu></HeaderNavMenu>
        <UserAvatar></UserAvatar>
      </Layout.Header>

      <Layout>
        {/* <Layout.Sider
          //  collapsible
          breakpoint="lg"
          collapsedWidth="0"
          width={180}
        >
          <SiderNavMenu></SiderNavMenu>
        </Layout.Sider> */}

        <Layout
          style={{
            padding: "0 24px 24px",
          }}
        >
          <Layout.Content
            style={{
              padding: 24,
              margin: 0,
            }}
          >
            <Outlet></Outlet>
          </Layout.Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
