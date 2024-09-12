import { Avatar } from "antd";
import { Button, Space, Table } from "antd";
import { useEffect } from "react";
import { useState, useRef } from "react";

import { TableProps } from "antd";
import CommonListPage from "./CommonListPage";
import { useNavigate } from "react-router-dom";




const CommonListTable = ({
  loading,
  dataSource,
  dataColumns,
  onTableChage,
  operationItems
}) => {
  const navigate = useNavigate();
  /**
   * @description 表格 column
   * @type {*} */
  const columns = [
    ...dataColumns,
    ...operationItems.map((item) => {
      return {
        title: item.label,
        fixed: "right",
        dataIndex: item.name,
        key: item.name,
        render: (_, record) => (
          <Button
            type="link"


            onClick={() => {
              // item.operation_view(record);
              console.log(item)
              const params = {}
              if (item.operation_type === "go_to_list") {
                for (const key in item.operation_map) {
                  params[key] = record[item.operation_map[key]]
                }
                const queryString = Object.keys(params).map(key => `${key}=${params[key]}`).join('&');
                navigate(`/${item.operation_view}?${queryString} `, {
                  state: {
                    id: record.id,
                    defaultParams: params
                  }
                });

              }
            }}
          >
            {item.label}
          </Button>
        ),
      };
    }),
  ];

  const tableRef = useRef();
  let [tableOffsetTop, setTableOffsetTop] = useState(0);
  console.log(operationItems)
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
      columns={columns}
      dataSource={dataSource}
      onChange={onTableChage}
      loading={loading}
      pagination={false}
      rowKey="id"
      scroll={{ x: 1300 }}
    ></Table>
  );
};

export default CommonListTable;
