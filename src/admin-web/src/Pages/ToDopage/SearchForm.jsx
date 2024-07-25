import { Button, Input } from "antd";
import { Select } from "antd";
import { Form } from "antd";
import { useForm } from "antd/es/form/Form";
import { DatePicker } from "antd";
import { stateList } from "./Components/stateMap";
import { priorityList } from "./Components/PriorityMap";
import { Space } from "antd";
import dayjs from "dayjs";

const SearchForm = ({ onSearch, onReset }) => {
  const [form] = useForm();
  const onClickReset = () => {
    form.resetFields();
    onReset();
  };

  const onFinish = (values) => {
    const searchParams = values;
    if (values.deadline !== undefined && values.deadline !== null) {
      searchParams.start_date = dayjs(values.deadline[0]).format("YYYY-MM-DD");
      searchParams.end_date = dayjs(values.deadline[1]).format("YYYY-MM-DD");
    }
    onSearch(searchParams);
  };

  return (
    <div className="search-form_container">
      <Form layout="inline" onFinish={onFinish} form={form}>
        <Space>
          <Form.Item label="待办标题" name="title">
            <Input placeholder="请输入" allowClear></Input>
          </Form.Item>
          <Form.Item label="待办状态" name="is_done">
            <Select
              style={{ minWidth: 120 }}
              // mode="multiple"
              placeholder="请选择"
              options={stateList}
              allowClear
            ></Select>
          </Form.Item>
          {/* <Form.Item label="优先级" name="priority">
          <Select
            style={{ minWidth: 120 }}
            mode="multiple"
            placeholder="请选择"
            options={priorityList}
          >
            <Select.Option></Select.Option>
          </Select>
        </Form.Item> */}
          <Form.Item label="截止日期" name="deadline">
            <DatePicker.RangePicker format="YYYY-MM-DD"></DatePicker.RangePicker>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                搜索
              </Button>
              <Button htmlType="submit" onClick={onClickReset}>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Space>
      </Form>
    </div>
  );
};

export default SearchForm;
