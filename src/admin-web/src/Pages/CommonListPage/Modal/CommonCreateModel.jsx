


import { Row, Button, Col, Input, Avatar } from "antd";
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


    const onOk = ()=>{
        setOpen(false)
        // setViewName("")
    }
    useEffect(()=>{
        if (viewName!="" && load){
            getViewInfo(viewName).then((res)=>{
                console.log(res)
                setOpen(true)

        })
    }
    },[viewName,load])

    return (
        <Modal
            open={open}
            onCancel={onCancel}
            onOk={onOk}
        >

        </Modal>
    )
}

export default CommonCreateModel;
