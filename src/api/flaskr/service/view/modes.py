from re import I
from arrow import get
from flask import Flask
from regex import D 
# from api.flaskr.service.study.coddnst import INPUT_TYPE_TEXT
from api.flaskr.service.common.dtos import PageNationDTO
from flaskr.dao import db
from sqlalchemy import Column, String, Integer, Date, TIMESTAMP, func
from flaskr.service.order.models import AICourseBuyRecord






INPUT_TYPE_TEXT = 'text'
INPUT_TYPE_DATE = 'date'
INPUT_TYPE_SELECT = 'select'
INPUT_TYPE_NUMBER = 'number'
INPUT_TYPE_DATETIME = 'datetime'
INPUT_TYPE_TIME = 'time'
INPUT_TYPE_CHECKBOX = 'checkbox'

# query list info 

class TableColumnItem:

    def __init__(self, column, lable):
        self.column =column # database column name
        self.lable = lable # table column lable name,display in page

    def __json__(self):
        return {
            "name": self.column,
            "lable": self.lable,
        }
    





# query input info
class InputItem:
        
        def __init__(self,column,lable,query_type, input_type,input_options=None,input_view = None):
            self.column = column
            self.lable = lable
            self.query_type = query_type
            self.input_type = input_type
            self.input_options = input_options
            self.input_view = input_view
    
        def __json__(self):
            return {
                "column": self.column,
                "lable": self.lable,
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
                    if input.fmt == 'like':
                        db_query = db_query.filter(getattr(self.model,key).like("%"+query.get(key)+"%"))
                    else:
                        db_query = db_query.filter(getattr(self.model,key) == query.get(key))
            count = db_query.count()
            if count == 0:
                return {}
            datas  = db_query.order_by(self.model.created.desc()).offset((page-1)*page_size).limit(page_size)
            items = [{'id':data.id,'data':{item.lable: str(getattr(data,item.column)) for item in self.items}} for data in datas]
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
    TableColumnItem('status','状态'),
    TableColumnItem('created','创建时间'),
    TableColumnItem('updated','更新时间')],
    [InputItem('user_id','用户ID','like',INPUT_TYPE_TEXT),
    InputItem('course_id','课程ID','like',INPUT_TYPE_TEXT),
    InputItem('price','价格','like',INPUT_TYPE_TEXT),
    InputItem('status','状态','like',INPUT_TYPE_TEXT),
    InputItem('created','创建时间','like',INPUT_TYPE_TEXT),
    InputItem('updated','更新时间','like',INPUT_TYPE_TEXT)],
    AICourseBuyRecord
    )