from flask import Flask







def get_view(app:Flask,user_id:str,view_name:str):
    with app.app_context():
        pass

def query_data(app:Flask,page:int=1,page_size:int=20,query=None):
    with app.app_context():
        app.logger.info("query:"+str(query)+" page:"+str(page)+" page_size:"+str(page_size))
        db_query = User.query
        if query:
            if query.get("mobile"):
                db_query = db_query.filter(User.mobile.like("%"+query.get("mobile")+"%"))
            if query.get("nickname"):
                db_query = db_query.filter(User.username.like("%"+query.get("nickname")+"%"))
            if query.get("user_id"):
                db_query = db_query.filter(User.user_id == query.get("user_id"))
        count = db_query.count()
        if count == 0:
            return {}
        users = db_query.order_by(User.created.desc()).offset((page-1)*page_size).limit(page_size)
        items =  [UserItemDTO(user.user_id,user.mobile,user.username,user.user