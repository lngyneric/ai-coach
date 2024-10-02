import {  Space } from "antd";
import SearchForm from "./SearchForm";
import CommonListTable from "./CommonListTable";
import { useEffect, useState } from "react";
import CommonCreateModel from "./Modal/CommonCreateModel";
import { useLocation } from "react-router-dom";
import { exportQuery } from "../../Api/manager";



import { Pagination } from "antd";

import {getViewInfo,queryView} from "../../Api/manager"
import { useParams } from "react-router-dom";


const CommonListPage = ({viewName}) => {
  const params = useParams()

  const [pageViewName,setPageViewName] = useState(viewName)
  const [createModelViewName,setCreateViewName] = useState("")
  const [createModelLoad,setCreateModelLoad] = useState(false)
  const [sort,setSort] = useState([])


  useEffect(()=>{
    // console.debug('viewName in useEffect ',viewName)
    if (viewName !== undefined) {
    setPageViewName(viewName)
    }else{
      console.debug('params.viewName in useEffect ',params.viewName)
      setPageViewName(params.viewName)
    }
  },[viewName])


  const queryStrings  = new URLSearchParams(useLocation().search)
  const defaultParams = {}
  queryStrings.forEach((value, key) => {
    defaultParams[key] = value
  });
  const [pageSize, setPageSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const [total, setTotal] = useState(0);
  /**
   * @description 查询参数
   */
  const [loading, setLoading] = useState(false);
  const [colum, setColum] = useState([]);
  const [searchParams, setSearchParams] = useState({});
  const [searchDefine,setSearchDefine]=useState({})
  const [operationItems,setOperationItems]=useState([])
  const [formOperationItems,setFormOperationItems]=useState([])
  /**
   *@description 点击搜索的方法
   *
   * @param {*} searchParams 搜索表单中的条件
   */
  const onSearch = (searchParams) => {
    setSearchParams(searchParams)
    setCurrentPage(1);
  };

  const onReset = (searchParams) => {
    setCurrentPage(1);
    searchParams(searchParams)
  };

  useEffect(() => {
    getViewInfo(pageViewName).then((res) => {
      const columns = res.data.items.map((item) => {
        return {
          title: item.lable,
          dataIndex: item.name,
          key: item.name,
        };
      });
      setOperationItems(res.data.operation_items)
      setFormOperationItems(res.data.form_operation)
      setColum(columns);
      setSearchDefine(res.data.queryinput);
      setSearchParams({})
      setCurrentPage(1)
      setSort([])
    });
  }, [pageViewName]);
  const [contactInfoList, setContactInfoList] = useState([]);
  /**
   * @description query data
   */
  const queryData = () => {
    setLoading(true);
    const params = {
      ...searchParams,
      ...defaultParams
    }
    console.log(params)
    console.log("sort",sort)
    queryView(pageViewName,currentPage,pageSize,params,sort)
      .then((res) => {
        setTotal(res.data.total);
        setContactInfoList(res.data.items);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  };

  const onPaginationChange = (page, pageSize) => {
    setCurrentPage(page);
    setPageSize(pageSize);
  }

  const onClickOperation = (operation) => {
    console.log(operation)
    setCreateViewName(operation.operation_view)
    setCreateModelLoad(true)
  }

  const onExport = (query) => {
    const params = {
      ...searchParams,
      ...defaultParams
    }
    console.log(params)
    exportQuery(pageViewName,params)
  }
  const onSortChange = (sorter) => {
    console.log(sorter)
    if (sorter.order !== undefined){
      // add to sort
      const sorterAdd = {column:sorter.field,order: sorter.order}
      const lastSort = sort.filter(item=>item.column !== sorter.field)
      console.log("lastSort",lastSort)
      setSort([...lastSort,sorterAdd])
    }else {
      // remove from sort
      setSort(sort.filter(item => item.column !== sorter.field))
    }
  }

  useEffect(() => {
  queryData()}, [pageSize,currentPage,searchParams,sort]);
  return (
    <Space direction="vertical" size="large" style={{ display: "flex" }}>
      <SearchForm onSearch={onSearch} onReset={onReset} inputs={searchDefine} operations = {formOperationItems} onClickOperation={onClickOperation} onExport={onExport}></SearchForm>
      <CommonListTable
        operationItems={operationItems}
        dataColumns={colum}
        dataSource={contactInfoList}
        loading={loading}
        onSortChange={onSortChange}
      ></CommonListTable>
      <Pagination pageSize={pageSize} onChange={onPaginationChange} current={currentPage} total={total} ></Pagination>
      <CommonCreateModel open={false} onCancel={()=>{}} onOk={()=>{}} viewName={createModelViewName} load={createModelLoad}></CommonCreateModel>
    </Space>
  );
};
export default CommonListPage;
