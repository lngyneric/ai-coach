from typing import List
from .models import ChatModel as Chat, ChatMsgModel as ChatMsg
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from ...dao import db
from ...plugin import GetAvaliableFuncs
import uuid
import json
import time
from datetime import datetime, timedelta, timezone
from .token import prompt_tokens_estimate

# 保存聊天记录
def save_chat(app: Flask, chat_id, user_id, chat_title, tokens, status):
    global db
    # db = SQLAlchemy(app)
    db.init_app(app)
    chat = Chat(chat_id=chat_id, user_id=user_id,
                chat_title=chat_title, tokens=tokens, status=status)
    db.session.add(chat)
    db.session.commit()
    return chat.id

class Msg:
    def __init__(self, msg, role, msg_type,id = None):
        self.msg = msg
        self.role = role
        self.type = msg_type
        self.id = id

    def __json__(self):
        return {
            'msg': self.msg,
            'role': self.role,
            'type': self.type
        }
def process_list(data):
    # 如果列表长度小于或等于10，直接返回原列表
    if len(data) <= 10:
        return data
    # 获取原列表的第一个元素和最后9个元素
    result = [data[0]] + data[-9:]

    # 检查result中的第二个元素（即原列表的倒数第9个元素）的type是否为'user'
    while result[1].get('role') != 'user':
        # 如果不是'user'，则删除这个元素
        del result[1]
        # 从原列表中选择一个type为'user'的元素添加到result中
        for item in reversed(data[:-9]):
            if item.get('role') == 'user':
                result.append(item)
                data.remove(item)
                break
    return result


class ChatInfo:
    def __init__(self, app: Flask, chat_id: str, user_id,created, chatMsg: List[ChatMsg]):
        self.chat_id = chat_id
        self.app = app
        self.created = created
        self.user_id = user_id
        self.chatMsg = []
        for msg in chatMsg:
            self.chatMsg.append(Msg(msg.msg, msg.role, msg.type))

    def addMsg(self, msg: Msg,trace):
        db_span = trace.span(name="db-save-message")
        self.chatMsg.append(msg)
        save_chat_msg(self.app, self.chat_id,self.user_id, msg.msg, msg.role, msg.type)
        db_span.end()

    def updateTitle(self, app: Flask, title):
        with app.app_context():
            chat = Chat.query.filter_by(chat_id=self.chat_id).first()
            chat.chat_title = title
            db.session.commit()

    def getMessageToSend(self):
        msgs = []
        for msg in self.chatMsg:
            if msg.type == "text":
                msgs.append(
                    {
                        "role": msg.role,
                        "content": msg.msg,
                    }
                )
            elif msg.type == "function_call":
                msgs.append(
                    {
                        "role": msg.role,
                        "content": "",
                        "tool_calls": [{"type":"function","function":json.loads(msg.msg),"id":msg.id}]
                    }
                )
            elif msg.role == "function":
                #msgs.append(
                #    {
                #        "role": msg.role,
                #        "name": msg.type,
                #        "content": msg.msg,
                #    }
                #)
                msgs.append(
                    {
                        "role": "tool",#msg.role,
                        # "name": msg.type,
                        "content": msg.msg,
                        "tool_call_id":msg.id
                    }
                )
        
        
        # 估算tokens
        # msgs = process_list(msgs)
        # self.app.logger.info("msgs:{}".format(msgs))
        return msgs


class ChatListItem:
    def __init__(self, chat_id, chat_title, tokens, date, status):
        self.chat_id = chat_id
        self.chat_title = chat_title
        self.tokens = tokens
        self.date = date
        self.status = status

    def __json__(self):
        return {
            "chat_id": self.chat_id,
            "chat_title": self.chat_title,
            "tokens": self.tokens,
            "status": self.status,
            'created': self.date.strftime("%Y-%m-%d %H:%M:%S")
        }

# 查找聊着记录
# 如果chat_id为空，则生成一个新的chat_id,同时插入一条chat_info
# 返回的为chat_id关联的chat_msg


def find_chat(app: Flask, user_id, chat_id="",  chat_title="", tokens=0, status=0) -> ChatInfo:
    # db = app.config["db"]
    with app.app_context():
        chat = Chat.query.filter_by(chat_id=chat_id, status=status).first()
        if chat is None:
            from ..user import get_user_info
            user_info = get_user_info(app, user_id)
            user_str = "用户名: "+user_info.name+" 用户邮箱: " + \
                user_info.email+" 用户电话: "+user_info.mobile
            chat_id = uuid.uuid1().hex
            chat = Chat(chat_id=chat_id, user_id=user_id,
                        chat_title=chat_title, tokens=tokens, status=status)
            db.session.add(chat)

            current_time = datetime.now(timezone(timedelta(hours=8)))
            format_time = current_time.strftime("%Y年%m月%d日 %H:%M %d")
            # 加入默认的 PLUGIN_CHAT_SYSTEM_MSG 消息
            chat_msg = ChatMsg(chat_id=chat_id, msg=app.config["PLUGIN_CHAT_SYSTEM_MSG"] +
                               "/r/n 当前系统时间为:"+format_time+"/r/n当前用户信息为: "+user_str, role="system", type="text")
            db.session.add(chat_msg)
            db.session.commit()
            return ChatInfo(app, chat_id, user_id, chat.created, [chat_msg])
        else:
            # 用chat_id查找chat_msg,order by id asc
            return ChatInfo(app, chat_id=chat_id,user_id=user_id, created=chat.created, chatMsg=ChatMsg.query.filter_by(chat_id=chat_id).order_by(ChatMsg.id.asc()).all())

# 保存一条chatMsg

def save_chat_msg(app: Flask,  chat_id,user_id, msg, role, msg_type):
    with app.app_context():
        chat_msg = ChatMsg(chat_id=chat_id, msg=msg, role=role, type=msg_type)
        db.session.add(chat_msg)
        if (role == "check"):
            chat = Chat.query.filter_by(chat_id=chat_id).first()
            chat.status = 1
        db.session.commit()
        return chat_msg

# 得到聊天记录列表
def get_chat_list(app: Flask, user_id: str, chat_title: str) -> List[ChatListItem]:
    # global db
    with app.app_context():
        chat_list = Chat.query.filter_by(
            user_id=user_id, status=0).filter(Chat.chat_title.like('%'+chat_title+'%')).order_by(Chat.id.desc()).all()
        return [ChatListItem(chat.chat_id, (chat.chat_title if chat.chat_title != "" else "历史会话"), chat.tokens, chat.created, chat.status) for chat in chat_list]
# 得到聊天记录


def get_chat(app: Flask, user_id, chat_id) -> List[Msg]:
    with app.app_context():
        available_functions = GetAvaliableFuncs(app, user_id)
        chat_msg_list = ChatMsg.query.filter(
            ChatMsg.chat_id == chat_id, ChatMsg.role != "system").order_by(ChatMsg.id.asc()).all()
        ret = []
        for chat_msg in chat_msg_list:
            if chat_msg.type == "text":
                ret.append(
                    {
                        "role": chat_msg.role,
                        "content": chat_msg.msg,
                    }
                )
            elif chat_msg.type == "function_call":
                app.logger.info("chat_msg.msg:{}".format(chat_msg.msg))
                ret.append(
                    {
                        "role": chat_msg.role,
                        "content": "",
                        "function_call": available_functions[json.loads(chat_msg.msg).get("name")]["msg"]
                    }
                )
            # else:
            #     ret.append(
            #         {
            #             "role": chat_msg.role,
            #             "name": chat_msg.type,
            #             "content": chat_msg.msg,
            #         }
            #     )
        return ret
