import { Avatar } from 'antd';
import { GithubOutlined } from '@ant-design/icons';

export const LogoCircle = ({ size = 64, style={} }) => {
  return <Avatar size={size} icon={<GithubOutlined />} style={style} />;
}

export default LogoCircle;
