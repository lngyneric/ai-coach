import { Row, Button, Col, Input,InputNumber, DatePicker,Select ,TimePicker} from "antd";
import { Form } from "antd";
import { Modal } from "antd";
import { useForm } from "antd/es/form/Form";
import { useEffect, useState } from "react";
import {getViewInfo} from "../../../Api/manager"
import {
  MinusCircleOutlined,
  PlusOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Upload } from "antd";

const CommonCreateModel = ({viewName,load})=>{

    const [open,setOpen] = useState(false)
    const [onCancel,setOnCancel] = useState(()=>{})
    const [formItems, setFormItems] = useState([]);
    const [operationItems, setOperationItems] = useState([]);
    const [form] = useForm();
    const onOk = ()=>{
        setOpen(false)
        // setViewName("")
    }
    useEffect(()=>{
        if (viewName!="" && load){
            getViewInfo(viewName).then((res)=>{
                const formItems = res.data.queryinput.map((input) => {
                    console.log(input)
                    if (input.input_type === "text") {
                        return (
                            <Form.Item
                                label={input.label}
                                name={input.name}
                                key={input.column}
                            >
                                <Input name={input.name} placeholder={input.placeholder} />
                            </Form.Item>
                        );
                    } else if (input.input_type === "options") {
                        return (
                            <Form.Item
                                label={input.label}
                                name={input.name}
                                key={input.column}
                            >
                                <Select options={input.input_options} placeholder={input.placeholder} />
                            </Form.Item>
                        );
                    }else if (input.input_type === "number") {
                    // Add more input types as needed
                    return (
                        <Form.Item
                            label={input.label}
                            name={input.name}
                            key={input.column}
                        >
                            <InputNumber placeholder={input.placeholder} />
                        </Form.Item>
                    );
                    }else if (input.input_type === "datetime") {
                        return (
                            <Form.Item
                                label={input.label}
                                name={input.name}
                                key={input.column}
                            >
                                <DatePicker placeholder={input.placeholder} />
                                {/* <TimePicker placeholder={input.placeholder} /> */}
                            </Form.Item>
                        );
                    }
                });
                const operationItems = res.data.operation_items.map((item)=>{
                    return (
                        <Button type="primary" onClick={()=>{
                            // item.operation(form.getFieldsValue())
                            console.log(form.getFieldsValue())
                        }}>{item.label}</Button>
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
        >
            <Form  className="detail-form" title="创建">
                {formItems}
            </Form>
            {operationItems}
        </Modal>
    )
}

export default CommonCreateModel;
