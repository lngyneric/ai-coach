import { Form, Input, DatePicker, TimePicker, Button } from "antd";
import { Modal } from "antd";
import dayjs, { Dayjs } from "dayjs";
import "./ScheduleDetailModal.css";
import { Empty } from "antd";
import { Divider } from "antd";
import { useEffect, useState } from "react";
import {
  GetScheduleDetails,
  UpdateSchedule,
  DeleteSchedule,
} from "../../../Api/schedule";
import { useForm } from "antd/es/form/Form";
import { Spin } from "antd";
import { Space } from "antd";

/**
 *
 * @param {*} param0 点击关闭的方法
 * @param {*} param0 点击删除的方法
 * @param {*} param0 点击保存方法
 * @returns
 */
const ModalFooter = ({ onClickCancel, onClickDelete, onClickCompleted }) => {
  return (
    <Space>
      <Button onClick={onClickCancel}> 关 闭 </Button>
      <Button danger onClick={onClickDelete}>
        删 除
      </Button>
      <Button type="primary" onClick={onClickCompleted}>
        保 存
      </Button>
    </Space>
  );
};

const ScheduleDetailModal = ({ open, scheduleId, onCompleted, onCancel }) => {
  const [form] = useForm();
  const [loading, setLoading] = useState(false);
  const queryScheduleDetail = () => {
    setLoading(true);
    GetScheduleDetails(scheduleId)
      .then((res) => {
        form.setFieldsValue({
          ...res.data,
          start: dayjs(new Date(res.data.start)),
          end: dayjs(new Date(res.data.end)),
        });
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  };

  const onOk = () => {
    form.validateFields().then((values) => {
      UpdateSchedule({
        schedule_id: scheduleId,
        ...values,
        starttime: dayjs(values.start).format("YYYY-MM-DD HH:mm:ss"),
        endtime: dayjs(values.end).format("YYYY-MM-DD HH:mm:ss"),
      }).then((res) => {
        onCompleted();
      });
    });
  };

  const onAfterOpenChange = (open) => {
    if (open) {
      queryScheduleDetail();
    }
  };

  const onClickDelete = () => {
    // 删除日程
    DeleteSchedule(scheduleId).then((res) => {
      onCompleted();
    });
  };

  return (
    <Modal
      forceRender
      title="日程详情"
      open={open}
      afterOpenChange={onAfterOpenChange}
      footer={
        <ModalFooter
          onClickCancel={onCancel}
          onClickCompleted={onOk}
          onClickDelete={onClickDelete}
        ></ModalFooter>
      }
    >
      <Spin spinning={loading}>
        <Form className="detail-form" form={form}>
          <Form.Item label="日程标题" name="description">
            <Input></Input>
          </Form.Item>
          <Divider></Divider>
          <Form.Item label="开始时间" name="start">
            <DatePicker showTime></DatePicker>
          </Form.Item>
          <Divider></Divider>
          <Form.Item label="截止时间" name="end">
            <DatePicker showTime></DatePicker>
          </Form.Item>
          <Form.Item label="地点" name="location">
            <Input placeholder="地点"></Input>
          </Form.Item>
          <Form.Item label="参与人" name="participants">
            <Input placeholder="参与人"></Input>
          </Form.Item>
          <Divider></Divider>
          <Form.Item label="备注" name="details">
            <Input.TextArea multiple="True"></Input.TextArea>
          </Form.Item>
        </Form>
      </Spin>
    </Modal>
  );
};

export default ScheduleDetailModal;
