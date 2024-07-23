from sqlalchemy import Column, String, Integer, TIMESTAMP, Text, Index, text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from ...dao import db


class ChatModel(db.Model):
    __tablename__ = 'chat_info'

    id = Column(BIGINT(unsigned=True), primary_key=True,
                autoincrement=True, comment='Unique ID')
    chat_id = Column(String(36), nullable=False, default='',
                     index=True, comment='Chat UUID')
    user_id = Column(String(36), nullable=False, default='',
                     index=True, comment='User UUID')
    chat_title = Column(String(255), nullable=False,
                        default='', comment='Title of the chat')
    tokens = Column(String(255), nullable=False, default='', comment='Tokens')
    status = Column(Integer, nullable=False, default=0,
                    comment='Status of the chat')
    created = Column(TIMESTAMP, nullable=False,
                     server_default=func.now(), comment='Creation time')
    updated = Column(TIMESTAMP, nullable=False, server_default=text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='Update time')


class ChatMsgModel(db.Model):
    __tablename__ = 'chat_msg'
    id = Column(BIGINT(unsigned=True), primary_key=True,
                autoincrement=True, comment='Unique ID')
    chat_id = Column(String(36), nullable=False, default='',
                     index=True, comment='Chat UUID')
    tokens = Column(String(255), nullable=False, default='', comment='Tokens')
    role = Column(String(255), nullable=False,
                  default='', comment='Role in the chat')
    type = Column(String(255), nullable=False, default='',
                  comment='Type of the message')
    function_info = Column(String(255), nullable=False,
                           default='', comment='Type of the message')
    msg = Column(Text, nullable=False, comment='Message content')
    created = Column(TIMESTAMP, nullable=False,
                     server_default=func.now(), comment='Creation time')
    updated = Column(TIMESTAMP, nullable=False, server_default=text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='Update time')
    status = Column(Integer, nullable=False, default=0,
                    comment='Status of the message')
