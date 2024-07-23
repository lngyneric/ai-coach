import { Tag } from "antd"
import './Tags.css';
import {priorityMap} from './PriorityMap';


const PriorityTags = ({priorityKey})=>{
    console.log(priorityKey);
    
    return (
    <Tag
        className="tag"
        color={priorityMap[priorityKey].color}>
        {priorityMap[priorityKey].label}
    </Tag>
    );
}

export default PriorityTags