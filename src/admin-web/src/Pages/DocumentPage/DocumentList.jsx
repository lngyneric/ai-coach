import { List, Skeleton} from "antd";
import './DocumentList.css'
import { Input, Button } from "antd";
import InfiniteScroll from 'react-infinite-scroll-component';
import { createFromIconfontCN } from '@ant-design/icons';
import { Dropdown } from "antd";
import { useState } from "react";
import { Empty } from "antd";
import { GetAllDocuments } from "../../Api/document";

/**
 * @description 排序选项
 */
const dropdownMenu = [
  {key:'nameAscendingOrder', label:"名称升序"},
  {key:'nameDescendingOrder', label:"名称降序"},
  {key:'timeAscendingOrder', label:"时间升序"},
  {key:'timeDescendingOrder', label:"时间降序"},
]

/**
 * @description 来自iconfont.cn 远程图标
 */
const IconFontSort = createFromIconfontCN({
  scriptUrl:"//at.alicdn.com/t/c/font_4167500_ekpu72ffhmt.js"
})

/**
 * @description 文档列表组件
 * @param {*} onClickListItem - 事件 点击列表中某一行的的方法 
 * @returns 
 */
const DocumentList = ({onClickListItem})=>{
    const [selectedSortOrder, setSelectedSortOrder] = useState();
    const [loading, setLoading] = useState();
    const [data, setData] = useState([]);

    const params = {};
    const dataLength = 100;
    
    

    const onSearch = (params)=>{
      console.log(params)
    }

    /**
     * @description 点击下拉菜单中的 排序选项的方法 实现单选 取消选择 的功能
     * @param {*} menuOption 
     */
    const onClickMenuItem = (menuOption)=> {
      if(menuOption.key === selectedSortOrder[0]){
        setSelectedSortOrder([])
        delete params.sortOrder;
      }
      else{
        setSelectedSortOrder([menuOption.key]);
        params.sortOrder = menuOption.key;
      }
    }


    const onNext = () => {
      setLoading(true);
      setTimeout(()=>{
        setLoading(false);
      }, 2000)
      console.log(`下一页`)
    }
    
    const listElement = ()=>{
      if(data.length>0){
        return (
          <div className="document_list_body">
            <InfiniteScroll
              dataLength={dataLength}
              next={onNext}
              hasMore={data.length < 50}
              loader={
                <Skeleton
                  loading={loading}
                  paragraph={{
                    rows: 1,
                  }}
                  active/>}
              scrollableTarget="document_list_container">
                  <List
                    loading={loading}
                    className="document_list"
                    dataSource={data}
                    renderItem={(item, index) => (
                        <List.Item>
                          <List.Item.Meta
                            title={<a
                                  onClick={()=>{onClickListItem(item)}}>
                                  {item.title}
                                </a>}
                          />
                          <div>{item.time}</div>
                        </List.Item>
                      )}>
                </List>
            </InfiniteScroll>
          </div>
        )
      }
      return (
        <div className="document_list_body__empty">
          <Empty
            description="暂无数据">
          </Empty>
        </div>
        
      )
    }
      

    useState(()=>{
      setLoading(true);
      GetAllDocuments().then((res)=>{
        setLoading(false);
        setData(res.data);
      }
      )
    },[])
      

    return (
        <div 
          id="document_list_container"
          className="document_list_container">
          <div className="documnet_list_header">
              <Input.Search
                onSearch={onSearch}
                placeholder="搜索文档">
              </Input.Search>
              <Dropdown
                menu={{
                  items:dropdownMenu,
                  selectable:true,
                  onClick: onClickMenuItem,
                  selectedKeys:selectedSortOrder
                  }}>
                <Button 
                  icon={<IconFontSort type="icon-icon-" />} />
              </Dropdown>
          </div>
            {listElement()}
        </div>

    );
}

export default DocumentList;