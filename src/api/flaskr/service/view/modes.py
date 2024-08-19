from re import I
from arrow import get
from flask import Flask
from regex import D 
# from api.flaskr.service.study.coddnst import INPUT_TYPE_TEXT
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
                    input = next(filter(lambda x: x.name == key, self.queryinput))
                    if input.fmt == 'like':
                        db_query = db_query.filter(getattr(self.model,key).like("%"+query.get(key)+"%"))
                    else:
                        db_query = db_query.filter(getattr(self.model,key) == query.get(key))
            count = db_query.count()
            if count == 0:
                return {}
            datas  = db_query.order_by(self.model.created.desc()).offset((page-1)*page_size).limit(page_size)

            items = [ {item.name: str(getattr(data,item.name)) for item in self.items} for data in datas]
            app.logger.info("query done"+str(items))
            return datas 
    def query_by_id(self,app:Flask,id):
        with app.app_context():
            app.logger.info("query_by_id:"+str(id))
            data  =  self.model.query.filter_by(id=id).first()
            if data == None:
                return {}
            items = {item.name: str(getattr(data,item.name)) for item in self.items}
    def query_by_id_and_property(self,app:Flask,id,property):
        with app.app_context():
            app.logger.info("query_by_id:"+str(id))
            data  =  self.model.query.filter_by(id=id).first()
            property_value = getattr(data,property)
            if property_value == None:
                return {}
            return views['xxx'].query_by_id(app,property_value)
    
        

OrderView = ViewDef('order',
                    [TableColumnItem('record_id','订单号',''),
                     TableColumnItem('price','订单状态',''),
                     TableColumnItem('paid_value','订单金额',''),
                     TableColumnItem('paid_value','订单时间','')],
                [InputItem('order_id','订单号','like')],AICourseBuyRecord)