import { Tag } from "antd";
import "./Tags.css";
import { stateMap } from "./stateMap";

const StateTags = ({ stateKey }) => {
  if (stateKey) {
    return (
      <Tag
        className="tag"
        style={{
          borderColor: stateMap[stateKey].color,
          color: stateMap[stateKey].color,
        }}
        color={stateMap[stateKey].backgroundColor}
      >
        {stateMap[stateKey].label}
      </Tag>
    );
  }
  return null;
};

export default StateTags;
