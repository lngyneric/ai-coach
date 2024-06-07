import {
  LogoutOutlined,
  SettingOutlined,
  UserAddOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Dropdown } from "antd";
import { Avatar } from "antd";
import { Link } from "react-router-dom";
import "./UserAvatar.css";
import { Space } from "antd";
import store from "store";

/**
 * @type {import("antd").MenuProps}
 */
const dropdownItems = [
  {
    key: "1",
    label: <Link to="/setting">系统设置</Link>,
    path: "/setting",
    icon: <SettingOutlined></SettingOutlined>,
  },
  {
    type: "divider",
  },
  {
    key: "2",
    label: <Link to="/login">退出登录</Link>,
    icon: <LogoutOutlined></LogoutOutlined>,
  },
];

const UserAvatar = () => {
  if (store.get("userInfo") === undefined) return false;
  const name = store.get("userInfo").name || "未设置用户名";
  const username = store.get("userInfo").username || "未设置用户名";
  return (
    <Dropdown menu={{ items: dropdownItems }}>
      <div className="user-avatar_container">
        <Space size="small">
          <Avatar
            className="avatar"
            size="large"
            shape="circle"
            style={{ backgroundColor: "#0096FF", fontSize: 18 }}
            icon={
              store.get("userInfo").name ? (
                name.substring(0, 1)
              ) : (
                <UserOutlined />
              )
            }
          >
            {name}
          </Avatar>
          <div className="userInfo">
            <span className="user-name">{name}</span>
            <span className="user-account-name">{username}</span>
          </div>
        </Space>
      </div>
    </Dropdown>
  );
};

export default UserAvatar;
