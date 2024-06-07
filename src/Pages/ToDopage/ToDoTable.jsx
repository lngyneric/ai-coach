import { Button, Space, Table } from "antd";
import { useState, useRef } from "react";
import StateTags from "./Components/StateTags";
import { useEffect } from "react";
import "./todoTable.css";
import dayjs from "dayjs";

/**
 * @description 获取所有的已完成状态的代办
 * @param {Array} dataSource - 外部的数据源
 */
const getDoneRow = (dataSource) => {
  const doneRows = dataSource.filter((row) => {
    return row.is_done === 1;
  });
  return doneRows;
};
const ToDoTable = ({
  loading,
  dataSource,
  onTableChage,
  onClickEdit,
  onTableSelectChange,
  onClickDelete,
}) => {
  /**
   * @description 表格 column
   * @type {*} */
  const columns = [
    {
      title: "标题",
      dataIndex: "title",
      key: "title",
      // sorter:{
      //   compare: true,
      // }
    },
    {
      title: "截止时间",
      dataIndex: "deadline",
      key: "deadline",
      // sorter:{
      // }
      render: (_, record) => {
        return dayjs(new Date(record.deadline)).format("YYYY-MM-DD HH:mm:ss");
      },
    },
    {
      title: "说明",
      dataIndex: "description",
      key: "description",
      // sorter:{
      // }
    },

    {
      title: "状态",
      dataIndex: "is_done",
      key: "is_done",
      // sorter:{compare: true,},
      render: (_, record) => {
        return (
          <StateTags
            stateKey={record.is_done ? "completed" : "toDo"}
          ></StateTags>
        );
      },
    },

    // {
    //   title: '优先级',
    //   dataIndex: 'priority',
    //   key: 'priority',
    //   sorter:{compare: true,},
    //   render: (_,record) => (
    //     <PriorityTags
    //       priorityKey={'high'}>
    //     </PriorityTags>
    //   )
    // },

    // {
    //   title: '截止日期',
    //   dataIndex: 'deadline',
    //   key:'deadline',
    //   sorter:{compare: true,}
    // },

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

  const tableRef = useRef();
  let [tableOffsetTop, setTableOffsetTop] = useState(0);

  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [innerLoading, setInnerLoading] = useState(loading);

  /**
   *
   *@description 表格选择项发生变化时的方法
   * @param {*} newSelectedRowKeys
   */
  const onSelectChange = (newSelectedRowKeys, selectedRow) => {
    if (selectedRowKeys.length > newSelectedRowKeys.length) {
      onTableSelectChange(selectedRowKeys.slice().pop());
    } else {
      onTableSelectChange(newSelectedRowKeys.slice().pop());
    }
    setSelectedRowKeys(newSelectedRowKeys);
  };

  useEffect(() => {
    const doneRows = getDoneRow(dataSource);
    const doneRwosKeyList = doneRows.map((row) => row.todo_id);
    setSelectedRowKeys(doneRwosKeyList);
  }, [dataSource]);

  return (
    <Table
      ref={tableRef}
      scroll={{ y: `calc(100vh - ${tableOffsetTop}px)` }}
      rowKey="todo_id"
      showSorterTooltip={false}
      rowSelection={{
        columnTitle: " ",
        selectedRowKeys,
        onChange: onSelectChange,
      }}
      columns={columns}
      dataSource={dataSource}
      onChange={onTableChage}
      loading={innerLoading}
      pagination={false}
    ></Table>
  );
};

export default ToDoTable;
