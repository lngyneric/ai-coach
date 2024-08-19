import { Button, Space, Modal } from "antd";
import SearchForm from "./SearchForm";
import CommonListTable from "./CommonListTable";
import { useEffect, useState } from "react";
import EditContactModal from "./Modal/EditContactModal";
import ContactDetailModal from "./Modal/ContactDetailModel";


import { Pagination } from "antd";

// import { GetAllContacts, deleteContact } from "../../Api/contact";
import {getUserList} from "../../Api/admin"

import { UploadEvent } from "../../Api/UploadEvent";
import { DeleteColumnOutlined, DeleteOutlined } from "@ant-design/icons";
import { TRUE } from "sass";
import { set } from "store";

const CommonListPage = () => {
  UploadEvent("ContactsComponant", { page: "contact" });


  const [pageSize, setPageSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const [total, setTotal] = useState(0);
  /**
   * @description 查询参数
   */
  const params = {};
  const [loading, setLoading] = useState(false);
  const [contactIds, setContactIds] = useState([]);
  /**
   *@description 点击搜索的方法
   *
   * @param {*} searchParams 搜索表单中的条件
   */
  const onSearch = (searchParams) => {
    Object.assign(params, searchParams);
    setCurrentPage(1);
    queryAllContacts();
  };

  const onReset = (searchParams) => {
    Object.assign(params, searchParams);
    queryAllContacts();
  };

  const [contactInfoList, setContactInfoList] = useState([]);
  /**
   * @description 联系人数据
   */
  const queryAllContacts = () => {
    getUserList(pageSize,currentPage,params)
      .then((res) => {
        setContactInfoList(res.data.items);
        setPageSize(res.data.page_size);
        setCurrentPage(res.data.page);
        setTotal(res.data.total);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  };
  /**
   * @description 联系人编辑表单 modal 的参数
   */
  const [editContactModalProps, setEditContactModalProps] = useState({
    open: false,
    state: "add",
    detailData: {},
  });

  /**
   * @description 查看联系详情的 Modal 的参数
   */
  const [contactDetailModalProps, setContactDetailModalProps] = useState({
    open: false,
    detailData: {},
  });

  /**
   * @description 点击新建联系人
   */
  const onClickCreateContact = () => {
    setEditContactModalProps({
      detailData: {},
      open: true,
      state: "add",
    });
  };

  /**
   * @description 关闭编辑联系人的 FromModal
   */
  const onEditContactCancel = () => {
    setEditContactModalProps({
      ...editContactModalProps,
      open: false,
    });
  };

  /**
   * @description 编辑联系人内 异步提交操作完成
   */
  const onEditAsyncOk = () => {
    setEditContactModalProps({
      ...editContactModalProps,
      open: false,
    });
    queryAllContacts();
  };

  /**
   *点击表格编辑的方法
   * @param {*} row
   */
  const onClickTableRowEdit = (row) => {
    console.log(row);
    setEditContactModalProps({
      open: true,
      state: "edit",
      detailData: row,
    });
  };

  /**
   *点击表格删除的方法
   *
   * @param {*} row
   */
  const onClickTableRowDelte = (row) => {
    Modal.confirm({
      title: "确认删除？",
      content: <p>删除后不可恢复，请谨慎操作！！！</p>,
      onOk: () => {
        // deleteContact([row.contact_id]).then((res) => {
        //   queryAllContacts();
        // });
      },
    });
  };

  /**
   * @description 点击表格中的详情的方法
   */
  const onClickTableDetail = (row) => {
    setContactDetailModalProps({
      open: true,
      detailData: row,
    });
  };

  /**
   * @description 联系人信息 Modal 关闭的方法
   */
  const onContactDetailModalCancel = () => {
    setContactDetailModalProps({
      ...contactDetailModalProps,
      open: false,
    });
  };

  /**
   * @description 点击批量删除的方法
   */
  const onClickDelete = () => {
    Modal.confirm({
      title: "确认删除？",
      content: <p>删除后不可恢复，请谨慎操作！！！</p>,
      onOk: () => {
        // deleteContact(contactIds).then((res) => {
          // queryAllContacts();
          // setContactIds([]);
        // });
      },
    });
  };

  const onTableSelectChange = (selectedRowKeys) => {
    console.log(selectedRowKeys);
    setContactIds(selectedRowKeys);
  };

  const onPaginationChange = (page, pageSize) => {
    setCurrentPage(page);
    setPageSize(pageSize);
  }

  useEffect(() => {
    setLoading(true);
    queryAllContacts();
  }, [pageSize,currentPage]);
  return (
    <Space direction="vertical" size="large" style={{ display: "flex" }}>
      <SearchForm onSearch={onSearch} onReset={onReset}></SearchForm>
      <CommonListTable
        dataSource={contactInfoList}
        onClickEdit={onClickTableRowEdit}
        onClickDelete={onClickTableRowDelte}
        onClickDetail={onClickTableDetail}
        loading={loading}
        onTableSelectChange={onTableSelectChange}
      ></CommonListTable>
      <Pagination pageSize={pageSize} onChange={onPaginationChange} current={currentPage} total={total} ></Pagination>
      <EditContactModal
        open={editContactModalProps.open}
        state={editContactModalProps.state}
        onCancel={onEditContactCancel}
        onAsyncOk={onEditAsyncOk}
        formData={editContactModalProps.detailData}
      ></EditContactModal>
      <ContactDetailModal
        open={contactDetailModalProps.open}
        detailData={contactDetailModalProps.detailData}
        onCancel={onContactDetailModalCancel}
      ></ContactDetailModal>
    </Space>
  );
};
export default CommonListPage;
