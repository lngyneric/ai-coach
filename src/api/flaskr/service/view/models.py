from tkinter import NO
from flask import Flask
from flaskr.service.common.dtos import PageNationDTO
from flaskr.dao import db
from sqlalchemy import Column, String, Integer, Date, TIMESTAMP, func
from flaskr.service.order.models import AICourseBuyRecord, DiscountRecord

from flaskr.service.order.consts import BUY_STATUS_VALUES,BUY_STATUS_TYPES, DISCOUNT_STATUS_TYPES, DISCOUNT_STATUS_VALUES,DISCOUNT_TYPE_VALUES,DISCOUNT_TYPE_TYPES,DISCOUNT_APPLY_TYPE_TYPES






INPUT_TYPE_TEXT = 'text'
INPUT_TYPE_DATE = 'date'
INPUT_TYPE_SELECT = 'select'
INPUT_TYPE_NUMBER = 'number'
INPUT_TYPE_DATETIME = 'datetime'
INPUT_TYPE_TIME = 'time'
INPUT_TYPE_CHECKBOX = 'checkbox'

# query list info 

class TableColumnItem:

    def __init__(self, column, lable,items=None):
        self.column =column # database column name
        self.lable = lable # table column lable name,display in page
        self.items = items

    def __json__(self):
        return {
            "name": self.column,
            "lable": self.lable,
        }
    





# query input info
class InputItem:
        
        def __init__(self,column,label,query_type, input_type,input_options = None,input_view = None):
            self.column = column
            self.label = label
            self.query_type = query_type
            self.input_type = input_type

            options = None
            if input_options!=None:
                options = []
                for key in input_options.keys():
                    options.append({"value":input_options.get(key),"label":key})
            self.input_options = options
            self.input_view = input_view
    
        def __json__(self):
            return {
                "column": self.column,
                "label": self.label,
                "query_type": self.query_type,
                "input_type": self.input_type,
                "input_options": self.input_options
            }


views = {}
class ViewDef:
    def __init__(self, name:str, items:list[TableColumnItem],queryinput:list[InputItem], model):
        self.name = name
        self.items = items
        self.model = model
        self.queryinput = queryinput
        views[name] = self
    
    def query(self,app:Flask,page:int=1,page_size:int=20,query=None):
        with app.app_context():
            app.logger.info("query:"+str(query)+" page:"+str(page)+" page_size:"+str(page_size))
            db_query = self.model.query
            if query:
                for key in query.keys():
                    input = next(filter(lambda x: x.column == key, self.queryinput))
                    if input.query_type == 'like':
                        db_query = db_query.filter(getattr(self.model,key).like("%"+str(query.get(key))+"%"))
                    else:
                        db_query = db_query.filter(getattr(self.model,key) == query.get(key))
            count = db_query.count()
            if count == 0:
                return {}
            datas  = db_query.order_by(self.model.id.desc()).offset((page-1)*page_size).limit(page_size) 

            
            items = [{'id':data.id,**{item.column: item .items.get(getattr(data,item.column),'') if item.items else str(getattr(data,item.column))  for item in self.items}} for data in datas]
            app.logger.info("query done"+str(items))
            return PageNationDTO(page,page_size,count,items)
    def query_by_id(self,app:Flask,id):
        with app.app_context():
            app.logger.info("query_by_id:"+str(id))
            data  =  self.model.query.filter_by(id=id).first()
            if data == None:
                return {}
            item = {'id':data.id,'data':{item.lable: str(getattr(data,item.column)) for item in self.items}}
            return item 
    def query_by_id_and_property(self,app:Flask,id,property):
        with app.app_context():
            app.logger.info("query_by_id:"+str(id))
            data  =  self.model.query.filter_by(id=id).first()
            property_value = getattr(data,property)
            if property_value == None:
                return {}
            return views['xxx'].query_by_id(app,property_value)
    def get_view_def(self):
        return {
            "name": self.name,
            "items": self.items,
            "queryinput": self.queryinput
        }
    
        

OrderView = ViewDef('order',
    [TableColumnItem('id','ID'),
    TableColumnItem('record_id','订单ID'),
    TableColumnItem('user_id','用户ID'),
    TableColumnItem('course_id','课程ID'),
    TableColumnItem('price','订单原价'),
    TableColumnItem('pay_value','应付金额'),
    TableColumnItem('discount_value','折扣金额'),
    TableColumnItem('status','状态',items=BUY_STATUS_VALUES),
    TableColumnItem('created','创建时间'),
    TableColumnItem('updated','更新时间')],
    [InputItem('user_id','用户ID','like',INPUT_TYPE_TEXT),
    InputItem('course_id','课程ID','like',INPUT_TYPE_TEXT),
    InputItem('price','价格','like',INPUT_TYPE_TEXT),
    InputItem('status','状态','like',INPUT_TYPE_TEXT,input_options=BUY_STATUS_TYPES),
    InputItem('created','创建时间','like',INPUT_TYPE_TEXT),
    InputItem('updated','更新时间','like',INPUT_TYPE_TEXT)],
    AICourseBuyRecord
    )


DisCountdRecordView = ViewDef('discount',
    [TableColumnItem('id','ID'),
    TableColumnItem('discount_value','折扣金额'),
    TableColumnItem('user_id','用户ID'),
    TableColumnItem('discount_code','折扣码'),
    TableColumnItem('discount_type','折扣类型',items=DISCOUNT_TYPE_VALUES),
    TableColumnItem('status','状态',items=DISCOUNT_STATUS_VALUES),
    TableColumnItem('created','创建时间'),
    TableColumnItem('updated','更新时间')],
    
    [
        InputItem('discount_value','折扣金额','like',INPUT_TYPE_TEXT),
        InputItem('status','状态','like',INPUT_TYPE_TEXT,input_options=DISCOUNT_STATUS_TYPES)
               ],
    DiscountRecord
    )