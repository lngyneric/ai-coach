import { Row, Button, Col, Input,InputNumber, DatePicker,Select ,TimePicker} from "antd";
import { Form } from "antd";
import { Modal } from "antd";
import { useEffect, useState } from "react";
import {getViewInfo} from "../../../Api/manager"
import {
  MinusCircleOutlined,
  PlusOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Upload } from "antd";
import dayjs from 'dayjs';

const CommonCreateModel = ({viewName,load})=>{

    const [open,setOpen] = useState(false)
    const [onCancel,setOnCancel] = useState(()=>{})
    const [formItems, setFormItems] = useState([]);
    const [operationItems, setOperationItems] = useState([]);
    const [form] = Form.useForm();
    const [formData,setFormData] = useState({})
    const onOk = async () => {
        try {
            const data = await form.validateFields();
            console.log(data);
            setOpen(false);
        } catch (error) {
            console.error("Validation failed:", error);
        }
    }

    const handleButtonClick = async (operation) => {
        try {
            console.log(formData)
            console.log(operation)
            const data = await form.validateFields();
            const operationData = {...formData,...data}
            console.log(operationData)
            // operation(form.getFieldsValue());
        } catch (error) {
            console.error("Validation failed:", error);
        }
    }

    useEffect(()=>{

        if (viewName!="" && load){
            getViewInfo(viewName).then((res)=>{
                const formItems = res.data.queryinput.map((input,index) => {
                    console.log(input)
                    if (input.input_type === "text") {
                        return (
                            <Form.Item
                                label={input.label}
                                name={input.column}
                                key={index}
                            >
                                <Input name={input.name} placeholder={input.placeholder} />
                            </Form.Item>
                        );
                    } else if (input.input_type === "options") {
                        return (
                            <Form.Item
                                label={input.label}
                                name={input.column}
                                key={index}
                                // key={input.column}
                            >
                                <Select key={input.name} options={input.input_options} placeholder={input.placeholder} />
                            </Form.Item>
                        );
                    }else if (input.input_type === "number") {
                    // Add more input types as needed
                    return (
                        <Form.Item
                            label={input.label}
                            name={input.column}
                            key={index}
                        >
                            <InputNumber key={input.name} placeholder={input.placeholder} />
                        </Form.Item>
                    );
                    }else if (input.input_type === "datetime") {
                        return (
                            <Form.Item
                                label={input.label}
                                // name={input.column}
                                key={index}
                            >
                                <DatePicker
                                    name={input.name}
                                    key={input.name}
                                    placeholder={input.placeholder}
                                    showTime
                                    onChange={(date, dateString) => {
                                        console.log({[input.column]:dateString})
                                        setFormData({...formData,[input.column]:dateString})
                                        // form.setFieldsValue({ [input.column]: dayjs(date).format('YYYY-MM-DD HH:mm:ss') });
                                    }}
                                />
                            </Form.Item>
                        );
                    }
                });
                const operationItems = res.data.operation_items.map((item,index)=>{
                    return (
                        <Button type="primary" text={item.label} key={index} onClick={() => handleButtonClick(item)}>
                            {item.label}
                        </Button>
                    )
                })
                setOperationItems(operationItems);
                setFormItems(formItems);
                setOpen(true)

        })
    }
    },[viewName,load])

    return (
        <Modal
            open={open}
            onCancel={onCancel}
            onOk={onOk}
            title="创建"
            footer={null}
        >
            <Form form={form} className="detail-form" title="创建">
                {formItems}
            </Form>
            {operationItems}
        </Modal>
    )
}

export default CommonCreateModel;
