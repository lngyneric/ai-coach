import { Button, Input } from "antd";
import { Form } from "antd";
import { Space } from "antd";
import { useForm } from "antd/es/form/Form";

const SearchForm = ({ onSearch, onReset }) => {
  const [form] = useForm();
  const onClickReset = () => {
    form.resetFields();
    onReset();
  };

  return (
    <div className="search-form_container">
      <Form
        layout="inline"
        onFinish={(vlaues) => {
          onSearch(vlaues);
        }}
        form={form}
      >
        <Space>
          <Form.Item label="UID" name="user_id">
            <Input allowClear placeholder="请输入"></Input>
          </Form.Item>
          <Form.Item label="联系电话" name="mobile">
            <Input allowClear placeholder="请输入"></Input>
          </Form.Item>
          <Form.Item label="昵称" name="nickname">
            <Input allowClear placeholder="请输入"></Input>
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
