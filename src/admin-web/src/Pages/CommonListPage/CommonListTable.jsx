import { Avatar } from "antd";
import { Button, Space, Table } from "antd";
import { useEffect } from "react";
import { useState, useRef } from "react";

import { TableProps } from "antd";




const CommonListTable = ({
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
    {
      title: "userId",
      dataIndex: "user_id",
      key: "user_id",
    },
    {
      title: "姓名",
      dataIndex: "name",
      key: "name",
    
    },

    {
      title: "电话",
      dataIndex: "mobile",
      key: "mobile",
    },

   
    {
      title: "性别",
      dataIndex: "user_sex",
      key: "user_sex",
    }, 
    {
      title: "生日",
      dataIndex: "birth",
      key: "birth",
    }, 
    {
      title: "操作",
      dataIndex: "action",
      key: "action",
      render: (_, record) => (
        <Space size="mini">
         <Button
            type="link"
            onClick={() => {
              onClickDetail(record);
            }}
          >
            详情
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


  const [top, setTop] = useState('topLeft');
  const [bottom, setBottom] = useState('bottomRight');


  return (
    <Table
      // pagination={{ position: [top, bottom] }}
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

export default CommonListTable;
