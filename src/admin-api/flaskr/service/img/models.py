
from ...dao import db
from sqlalchemy import Column, String, Integer,DateTime,Boolean, TIMESTAMP, Text, Index, text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

class Image(db.Model):
    __tablename__ = 'chat_img'

    id = Column(BIGINT, primary_key=True, comment='Unique ID', autoincrement=True)
    img_id = Column(String(36), nullable=False, default='', comment='Image UUID')
    chat_id = Column(String(36), nullable=False, default='', comment='Chat UUID')
    user_id = Column(String(36), nullable=False, default='', comment='User UUID')
    bucket_id = Column(String(36), nullable=False, default='', comment='Bucket UUID')
    prompt = Column(Text, nullable=False, comment='Prompt for the image')
    size = Column(String(50), nullable=False, default='', comment='Size of the image')
    url = Column(Text, nullable=False, comment='URL of the image')
    bucket_base = Column(Text, nullable=False, comment='Bucket Base URL')
    created = Column(TIMESTAMP, nullable=False, default=func.now(), comment='Creation time')
    updated = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now(), comment='Update time')

    def __init__(self, img_id, chat_id, user_id, bucket_id, prompt, size, url, bucket_base):
        self.img_id = img_id
        self.chat_id = chat_id
        self.user_id = user_id
        self.bucket_id = bucket_id
        self.prompt = prompt
        self.size = size
        self.url = url
        self.bucket_base = bucket_base
