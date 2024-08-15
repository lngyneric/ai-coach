



# 装饰器函数，用于跳过Token校验
from functools import wraps
from trace import Trace

from flask import Flask

from flaskr.service.lesson.models import AILessonScript
from flaskr.service.order.models import AICourseLessonAttend


class BreakException(Exception):
    pass

UI_HANDLE_MAP = {
}
def register_input_handler(input_type:str):
    def decorator(func):
        print(f"register_input_handler {input_type} ==> {func.__name__}")
        UI_HANDLE_MAP[input_type] = func
        return func
    return decorator
   


def handle_input(app:Flask,user_id:str,input_type:str,attend:AICourseLessonAttend,script_info:AILessonScript,input:str,trace:Trace,trace_args
):
    app.logger.info(f"handle_input {input_type},user_id:{user_id},input:{input} ")
    if input_type in UI_HANDLE_MAP:
        respone =  UI_HANDLE_MAP[input_type](app,user_id,attend,script_info,input,trace,trace_args)
        if respone:
            yield from respone
    else:
        return None
    

