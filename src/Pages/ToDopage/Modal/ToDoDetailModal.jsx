import { Form } from "antd";
import { Modal } from "antd";
import StateTags from "../Components/StateTags";
import PriorityTags from "../Components/PriorityTags";
import dayjs from "dayjs";
import "./ToDoDetailModal.css";
import { Empty } from "antd";
import { Divider } from "antd";

/**
 * @description 处理备注字段没有数据时的
 * @param {*}
 * @returns
 */
const RemarkInfo = ({ remark }) => {
  if (remark) {
    return { remark };
  } else {
    return <Empty></Empty>;
  }
};

const ToDoDetailModal = ({ open, detailData, onCompleted, onCancel }) => {
  const onOk = () => {
    onCompleted(detailData);
  };

  return (
    <Modal
      forceRender
      title="待办详情"
      open={open}
      okText="编辑"
      cancelText="关闭"
      onOk={onOk}
      onCancel={onCancel}
    >
      <Form className="detail-form">
        <Form.Item label="待办标题">
          <span>{detailData.name}</span>
        </Form.Item>
        <Divider></Divider>
        <Form.Item label="待办状态">
          <StateTags stateKey={detailData.state} />
        </Form.Item>
        <Divider></Divider>
        <Form.Item label="优先级">
          <PriorityTags priorityKey={detailData.priority} />
        </Form.Item>
        <Divider></Divider>
        <Form.Item label="截止日期">
          <span>{dayjs(detailData.deadline).format("YYYY-MM-DD")}</span>
        </Form.Item>
        <Divider></Divider>
        <Form.Item label="备注">
          <div className="remark-container">
            <RemarkInfo remark={detailData.remark}></RemarkInfo>
          </div>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ToDoDetailModal;
