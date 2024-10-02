import { Button, Table } from "antd";
import { useEffect } from "react";
import { useState, useRef } from "react";

import { useNavigate } from "react-router-dom";

const CommonListTable = ({
  loading,
  dataSource,
  dataColumns,
  onTableChage,
  operationItems,
  onSortChange // 新增的回调函数
}) => {
  const navigate = useNavigate();
  /**
   * @description 表格 column
   * @type {*} */
  const columns = [
    ...dataColumns.map(column => ({
      ...column,
      sorter: true, // 添加排序功能
    })),
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
  useEffect(() => {
    setTableOffsetTop(tableRef.current.offsetTop + 60);
  }, [tableOffsetTop]);

  const handleTableChange = (pagination, filters, sorter) => {
    if (onTableChage) {
      onTableChage(pagination, filters, sorter);
    }
    if (onSortChange) {
      onSortChange(sorter); // 调用排序变化的回调函数
    }
  };

  return (
    <Table
      ref={tableRef}
      scroll={{ y: `calc(100vh - ${tableOffsetTop}px)` }}
      showSorterTooltip={false}
      columns={columns}
      dataSource={dataSource}
      onChange={handleTableChange} // 使用新的回调函数
      loading={loading}
      pagination={false}
      rowKey="id"
      scroll={{ x: 1300 }}
      sortDirections={['ascend', 'descend']} // 支持多列排序
    ></Table>
  );
};

export default CommonListTable;
