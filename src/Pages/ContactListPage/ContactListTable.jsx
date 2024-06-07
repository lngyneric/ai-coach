import { Avatar } from "antd";
import { Button, Space, Table } from "antd";
import { useEffect } from "react";
import { useState, useRef } from "react";

const ContactListTable = ({
  loading,
  dataSource,
  onTableChage,
  onClickDetail,
  onClickEdit,
  onClickDelete,
  onTableSelectChange,
}) => {
  /**
   * @description 表格 column
   * @type {*} */
  const columns = [
    // {
    //   title:"编号",
    //   dataIndex:"number",
    //   key:"number",
    // },
    {
      title: "头像",
      dataIndex: "avatar",
      key: "avatar",
      render: (value, record) => (
        <Avatar src={value}>{record.name.slice(0, 1)}</Avatar>
      ),
    },
    {
      title: "姓名",
      dataIndex: "name",
      key: "name",
      // sorter: {
      //   compare: true,
      // },
    },

    {
      title: "联系电话",
      dataIndex: "mobile",
      key: "mobile",
    },

    {
      title: "邮箱地址",
      dataIndex: "email",
      key: "email",
    },

    {
      title: "操作",
      dataIndex: "action",
      key: "action",
      render: (_, record) => (
        <Space size="mini">
          {/* <Button
            type="link"
            onClick={() => {
              onClickDetail(record);
            }}
          >
            详情
          </Button> */}
          <Button
            type="link"
            onClick={() => {
              onClickEdit(record);
            }}
          >
            编辑
          </Button>
          <Button
            type="link"
            onClick={() => {
              onClickDelete(record);
            }}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const tableRef = useRef();
  let [tableOffsetTop, setTableOffsetTop] = useState(0);
  /**
   *
   *@description 表格选择项发生变化时的方法
   * @param {*} newSelectedRowKeys
   */
  const onSelectChange = (newSelectedRowKeys) => {
    setSelectedRowKeys(newSelectedRowKeys);
    onTableSelectChange(newSelectedRowKeys);
  };
  useEffect(() => {
    console.log(tableRef.current);
    setTableOffsetTop(tableRef.current.offsetTop + 60);
    console.log(tableOffsetTop);
  }, [tableOffsetTop]);
  return (
    <Table
      ref={tableRef}
      scroll={{ y: `calc(100vh - ${tableOffsetTop}px)` }}
      showSorterTooltip={false}
      rowSelection={{ selectedRowKeys, onChange: onSelectChange }}
      columns={columns}
      dataSource={dataSource}
      onChange={onTableChage}
      loading={loading}
      pagination={false}
      rowKey="contact_id"
    ></Table>
  );
};

export default ContactListTable;
