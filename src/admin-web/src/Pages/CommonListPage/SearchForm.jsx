import { Button, Input ,Select } from "antd";
import { Form } from "antd";
import { Space } from "antd";
import { useForm } from "antd/es/form/Form";
import { useNavigate } from "react-router-dom";

const SearchForm = ({ onSearch, onReset,inputs }) => {
  const [form] = useForm();
  const navigate = useNavigate();
  const onClickReset = () => {
    form.resetFields();
    onReset();
  };


  function loadInputs(inputs){
    let ret = []
     for (let i = 0 ;i < inputs.length;i++){
        let input = inputs[i];
        let {label,column} = input;
        if (input.input_options){

          ret.push( (
            <Form.Item label={label} name={column} >
              <Select allowClear  options = {input.input_options}  placeholder="请选择">


              </Select>
            </Form.Item>)
          )

        }else {
        ret.push( (
          <Form.Item label={label} name={column} >
            <Input allowClear placeholder="请输入"></Input>

          </Form.Item>
        ))
      }
     }
      return ret;
  }

  const onClickBack = () => {
    navigate(-1)
  }

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
          {loadInputs(inputs)}
          <Form.Item style={{ float: 'right' }}>
            <Space>
              <Button type="primary" htmlType="submit">
                搜索
              </Button>
              <Button htmlType="submit" onClick={onClickReset}>
                重置
              </Button>
              <Button htmlType="" onClick={onClickBack}>
                返回
              </Button>
            </Space>
          </Form.Item>
        </Space>
      </Form>
    </div>
  );
};

export default SearchForm;
