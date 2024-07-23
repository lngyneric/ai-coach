import { Space } from "antd";
import SearchForm from "./SearchForm";
import ToDoTable from "./ToDoTable";
import EditToDoModal from "./Modal/EditToDoModal";
import ToDoDetailModal from "./Modal/ToDoDetailModal";
import { useEffect, useState } from "react";
import { Modal } from "antd";
import { GetAllTodos, MarkTodo, deleteTodo } from "../../Api/todo";
import { UploadEvent } from "../../Api/UploadEvent";

const ToDoComponent = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    UploadEvent("GetAllTodos", { page: "todo" });
    GetAllTodos().then((res) => {
      setLoading(false);
      setData(res.data);
    });
  }, []);

  const params = {};

  const [editToDoModalProps, setEditToDoModalProps] = useState({
    open: false,
    state: "add",
    detailData: {},
  });

  const [toDoDetailModalProps, setToDoDetailModalProps] = useState({
    open: false,
    detailData: {},
  });

  /**
   *@description 点击搜索的方法
   *
   * @param {*} searchParams 搜索表单中的条件
   */
  const onSearch = (searchParams) => {
    Object.assign(params, searchParams);
    console.log(params);
    queryData();
  };

  const onReset = (searchParams) => {
    Object.assign(params, searchParams);
    queryData();
  };

  /**
   *
   *@description 表格选择项发生变化时的方法
   * @param {*} newSelectedRowKeys - 当前操作行的 key
   */
  const onSelectChange = (currentRowkey) => {
    console.log("selectedRowKeys changed: ", currentRowkey);
    setLoading(true);
    MarkTodo(currentRowkey).then(() => {
      queryData();
    });
  };

  /**
   * @description 表格控件发生变化后 设置查询参数。
   *
   * @param {*} pagination 分页参数
   * @param {*} filters 筛选参数
   * @param {*} sorter 排序参数
   * @param {*} extra
   */
  const onTableChage = (pagination, filters, sorter, extra) => {
    Object.assign(params, { pagination }, { sorter });
    queryData();
  };

  /**
   *点击表格删除的方法
   *
   * @param {*} row
   */
  const onClickTableRowDelte = (row) => {
    console.log(row);
    Modal.confirm({
      title: "确认删除？",
      content: <p>删除后不可恢复，请谨慎操作！！！</p>,
      onOk: () => {
        deleteTodo(row.todo_id).then(() => {
          queryData();
        });
      },
    });
  };

  /**
   *点击表格编辑的方法
   * @param {*} row
   */
  const onClickTableRowEdit = (row) => {
    console.log(row);
    setEditToDoModalProps({
      open: true,
      state: "edit",
      detailData: row,
    });
  };

  /**
   *点击详情的方法
   * @param {*} row
   */
  const onClickDetail = (row) => {
    console.log(row);
    setToDoDetailModalProps({
      open: true,
      detailData: row,
    });
  };

  /**
   *@description 编辑 todo modal 点击关闭时的方法
   *
   */
  const onEditToDoModalCancel = () => {
    setEditToDoModalProps({
      open: false,
    });
  };

  /**
   *@description 点击创建 to do 的方法
   *
   */
  const onClickCreateToDo = () => {
    setEditToDoModalProps({
      open: true,
      state: "add",
    });
  };

  /**
   * 添加修改 todo 的 modal 提交成功后的方法
   *
   */
  const onEditToDoModalOk = () => {
    setEditToDoModalProps({
      open: false,
    });
    queryData();
  };

  const onToDoDetailModalCompleted = (detailData) => {
    setEditToDoModalProps({
      open: true,
      state: "edit",
      detailData,
    });
    setToDoDetailModalProps({
      ...toDoDetailModalProps,
      open: false,
    });
  };

  const onToDoDetailModelCancel = () => {
    setToDoDetailModalProps({
      ...toDoDetailModalProps,
      open: false,
    });
  };

  /**
   *@description 查询数据的方法
   */
  const queryData = () => {
    GetAllTodos(
      params.title,
      params.is_done,
      params.start_date,
      params.end_date
    )
      .then((res) => {
        setLoading(false);
        setData(res.data);
      })
      .catch(() => {
        setLoading(false);
      });
  };

  return (
    <Space
      className="todo_page"
      direction="vertical"
      size="large"
      style={{ display: "flex" }}
    >
      <SearchForm onSearch={onSearch} onReset={onReset}></SearchForm>

      <Space>
        {/* <Button
            type="primary"
            onClick={onClickCreateToDo}>
            添加待办
          </Button> */}
      </Space>

      <ToDoTable
        dataSource={data}
        onTableChage={onTableChage}
        onClickTableRowDelte={onClickTableRowDelte}
        onClickDetail={onClickDetail}
        onClickDelete={onClickTableRowDelte}
        onClickEdit={onClickTableRowEdit}
        onTableSelectChange={onSelectChange}
        loading={loading}
      ></ToDoTable>

      <EditToDoModal
        open={editToDoModalProps.open}
        state={editToDoModalProps.state}
        formData={editToDoModalProps.detailData}
        onCancel={onEditToDoModalCancel}
        onAsyncOk={onEditToDoModalOk}
      />

      <ToDoDetailModal
        open={toDoDetailModalProps.open}
        onCompleted={onToDoDetailModalCompleted}
        onCancel={onToDoDetailModelCancel}
        detailData={toDoDetailModalProps.detailData}
      />
    </Space>
  );
};

export default ToDoComponent;
