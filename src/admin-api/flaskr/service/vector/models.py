from pymilvus import utility
from pymilvus import connections
from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, IndexType, Status
from flask import Flask
import openai
import uuid
openai.api_key = "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" # geyf@me.com
openai.api_base = "https://openai-api.kattgatt.com/v1"

def getUserCollection(app: Flask, user_id: str):
    # utility.drop_collection('chat_msg')
    with app.app_context():
        if utility.has_collection('chat_msg') == False:
            ## create collection
            id = FieldSchema(
            name="id",
            dtype=DataType.VARCHAR,
            is_primary=True,
            max_length=36,
            )
            chat_id = FieldSchema(
            name="chat_id",
            dtype=DataType.VARCHAR,
            max_length=36,
            )
            chat_role = FieldSchema(
                name="chat_role",
                dtype=DataType.VARCHAR,
                max_length=36,
            )
            user_id = FieldSchema(
                name="user_id",
                dtype=DataType.VARCHAR,
                max_length=36,
                index=True,
            )
            word_count = FieldSchema(
            name="word_count",
            dtype=DataType.INT64,
            )
            index  = FieldSchema(
                name="index",
                dtype=DataType.FLOAT_VECTOR,
                dim=1536,
            )
            text = FieldSchema(
                name="text",
                dtype=DataType.VARCHAR,
                max_length=1024
            )
            schema = CollectionSchema(
                fields=[id,chat_id, user_id,chat_role, word_count, index, text],
                description="The collection of user",
                enable_dynamic_field=True,
                collection_name = 'chat_msg'
            )
            collection = Collection(
                name='chat_msg',
                schema=schema,
                using='default',
                shards_num=2
                )
            # create index
            collection.create_index(
                field_name="index",
                index_params={"metric_type": "L2"},
                index_type=IndexType.IVF_FLAT,
                # index_type=IndexType.FLAT,
            )
            
            app.logger.info("create collection {}".format(user_id))
            return collection
        else:
            ret =  Collection('chat_msg')
            ret.load()
            return ret



def split_string(text,length,overlap):
    ret = []
    for i in range(0,len(text),length-overlap):
        ret.append(text[i:i+length])
    return ret
def save_text_to_collection(app:Flask,user_id,chat_id,role,text):
    with app.app_context():
        # 拆分text
        app.logger.info("save_text_to_collection {} {} {}".format(user_id,role,text))
        texts = split_string(text.replace("\n",""),512,64)
        for save_text in texts:
            id = str(uuid.uuid4()).replace('-', '')
            vector = openai.Embedding.create(
                input=[save_text],
                model = "text-embedding-ada-002"
            )['data'][0]['embedding']
            collection = getUserCollection(app,user_id)
            collection.insert(
                [
                    {
                        "id":id,
                        "chat_id":chat_id,
                        "user_id":user_id,
                        "chat_role":role,
                        "word_count":len(save_text),
                        "index":vector,
                        "text":save_text
                    }
                ]
            )
        return 'save success'
def search_text(app:Flask,user_id,text):
    with app.app_context():
        vector = openai.Embedding.create(
            input=[text],
            model = "text-embedding-ada-002"
        )['data'][0]['embedding']
        collection = getUserCollection(app,user_id)
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10},
            "limit": 10,
            "round_decimal": 3,
            "expr": "user_id = '"+user_id+"'",
          
        }
        results = collection.search(
            data=[vector],
            anns_field="index",
            param=search_params,
            limit=5,
            output_fields = ["text"]
        )
        app.logger.info("results:{}".format(results))
        ret = [result.entity.get("text") for result in results[0]]
        app.logger.info("search :{} result :{}".format(text,ret))
        return  str(ret)
    