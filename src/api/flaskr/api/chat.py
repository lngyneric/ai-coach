import datetime
import random
import openai
from openai.types.chat import  ChatCompletionSystemMessageParam,ChatCompletionUserMessageParam,ChatCompletionAssistantMessageParam,ChatCompletionToolMessageParam,ChatCompletionFunctionMessageParam,ChatCompletionMessageParam,ChatCompletionToolParam
import json
import time
import uuid
import chardet
from flask import Flask,g,request

from . livedata import check
from .. service import check_risk as check_risk_service
import traceback
# from .llm.glm import get_chat_response as zhipuchat
from .llm.minimaxChat import miniMaxChat




client = openai.Client(api_key="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",base_url="https://openai-api.kattgatt.com/v1")
def ChatFunc(app :Flask,text):
    return ChatFunSSE(app, text)
def get_current_time(app):
    # 返回当前系统时间，格式为：2021年3月1日 12:00，用到的函数为time.strftime("%Y年%m月%d日 %H:%M", time.localtime())
    # 得到星期几
    # 
    app.logger.info("获取当前时间{}".format(time.strftime("%Y年%m月%d日 %H:%M %d", time.localtime())))
    return time.strftime("%Y年%m月%d日 %H:%M %D", time.localtime()) 


def fmt(o):
    if isinstance(o, datetime.datetime):
        return o.isoformat()
    

def invokeChat(app:Flask ,model:str,prompt:str):
    # model = "abab6-chat"
    # for msg in zhipuchat(app,prompt):
    #     if msg.choices and len(msg.choices)>0  and msg.choices[0].delta and msg.choices[0].delta.content:
    #         yield msg.choices[0].delta.content
    response = client.chat.completions.create(
       model="GPT-4-US",
       messages=[{"content":prompt,"role":"user"}],
       temperature=0,
       stream=True,
    )
    for msg in response:
       if msg.choices and len(msg.choices)>0  and msg.choices[0].delta and msg.choices[0].delta.content:
           yield msg.choices[0].delta.content

def ChatFunSSE(app : Flask, text,chating_id,user_id,model="gpt-4"):
    model ="gpt-4"
    from .. api.langfuse import langfuse_client as langfuse
    reqtext = text
    chatInfo  = chat_service.find_chat(app,user_id,chat_id=chating_id)
    chatId = chatInfo.chat_id
    functions = plugin.GetFuncs(app,user_id)
    available_functions = plugin.GetAvaliableFuncs(app,user_id)

    check_span_args ={}
    check_span_args['name'] = "livedata_check"
    check_span_args['input'] = reqtext
 

    trace_args ={}
    trace_args['user_id'] = user_id
    trace_args['session_id'] = chatId
    trace_args['metadata'] = {"chat_id":chatId,"model":model}
    trace_args['input'] = reqtext 
    trace_args['name'] = "ai-assistant"
    trace = langfuse.trace(**trace_args)
    check_span = trace.span(**check_span_args)
 
    chatInfo.addMsg(chat_service.Msg(msg=reqtext,role="user",msg_type="text"),check_span)


    resp = check(app,reqtext,user_id)
    check_span_args['output'] = resp
    is_pass = 1
    check_rest = resp.get("textSpam",{}).get("result",{})
    
    if(check_rest == 2):
        is_pass = 0
    db_span = check_span.span(name="db")
    check_risk_service.add_risk_control_result(app,chatId,user_id,reqtext,"livedata",check_rest,json.dumps(resp),is_pass,"strong") 
    db_span.end()

    check_span.update(**check_span_args)
      
    if check_rest == 2:
        text = "您的发言包含敏感词汇，已被系统拦截"
        chatInfo.addMsg(chat_service.Msg(msg=text,role="check",msg_type="text"),trace=trace)
        data =  {
                    'type': 'content',
                    'text': text, 
                    'chat_id': chatId
                }
        msg =  'data: '+json.dumps(data)+'\n\n'
        yield msg
        check_span.end() 
        return
     
    check_span.end() 
    new_chat = False
    is_calling = True
    args = {}
    # if len(functions)>0:
        # args["tools"] = get_openai_tools(functions)
        
    try:
        while is_calling:
            is_calling = False
            app.logger.info("text:{}".format(text))
            messages = chatInfo.getMessageToSend()

            # messages = get_openai_messages(messages)
            app.logger.info("messages:{}".format(messages))
            span = trace.span(name="gpt-call-chat")
            generator = span.generation(name="web-assistant",model=model,   input={"messages":messages,"functions":functions})
            if len(chatInfo.getMessageToSend()) == 2:
                new_chat = True
            role = ""
            text = ""
            functions_call = []
            response =client.chat.completions.create(
                model="GPT-4-US",
                
                messages=get_openai_messages(messages),
                temperature=0,
                stream=True,
                   **args
                )
            app.logger.info("response:{}".format(response))
            try:
                for msg in response:
                    app.logger.info("msg:{}".format(msg))
                    if len(msg.choices)>0 :
                        if  msg.choices[0].delta.role:
                            role =  msg.choices[0].delta.role
                        if msg.choices[0].delta.content:
                            text = text+ msg.choices[0].delta.content
                            data =  {
                                    'type': 'content',
                                    'text':  msg.choices[0].delta.content,
                                    'chat_id': chatId
                                }
                            yield  'data: '+json.dumps(data)+'\n\n'
                        if msg.choices[0].delta.tool_calls and len(msg.choices[0].delta.tool_calls)>0:
                            for tool_call in msg.choices[0].delta.tool_calls:
                                if tool_call.function.name:
                                    functions_call.append({"name":tool_call.function.name,"arguments":""})
                                    is_calling = True
                                    yield 'data: {"type":"calling","function_name":"%s","chat_id":"%s"}\n\n'%(available_functions[tool_call.function.name]["msg"],chatId)
                                if tool_call.id:
                                    functions_call[-1]["id"] = tool_call.id
                                functions_call[-1]["arguments"] = functions_call[-1]["arguments"] + tool_call.function.arguments #.encode('utf-8').decode(detected_encoding)
                                app.logger.info("functions_call:{}".format(functions_call))
            except Exception as e:
                is_calling = False
                app.logger.error(traceback.format_exc())
                role = ""
                text = ""
                function_args=""
                functions_call = []
                response =client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0,
                    **args
                    )
                app.logger.info("stream 出错,重新请求")
                app.logger.info("response:{}".format(response))
                if response.choices[0].message.role:
                    role =  response.choices[0].message.role
                if response.choices[0].message.content:
                    text = text+ response.choices[0].message.content
                if response.choices[0].message.tool_calls and len(response.choices[0].message.tool_calls)>0:
                    is_calling = True
                    for tool_call in response.choices[0].message.tool_calls:
                        if tool_call.function.name:
                            detected_encoding = chardet.detect(tool_call.function.arguments.encode('utf-8'))['encoding']
                            app.logger.info("detected_encoding:{}".format(detected_encoding))
                            functions_call.append({"name":tool_call.function.name,"arguments":tool_call.function.arguments.encode('utf-8').decode(detected_encoding)})
                            is_calling = True
                            app.logger.info("functions_call:{}".format(functions_call))
                
         
            if is_calling:
                app.logger.info("functions_call:{}".format(functions_call))
                generator.end(
                    output=functions_call
                )
                for call in functions_call:
                    tool_call_name = call["name"]
                    call_args = json.loads(call["arguments"],strict = False)
                    call_span = span.span(name=tool_call_name,input=call_args)
                    app.logger.info("tool_call_name:{},arguments:{}".format(tool_call_name,call_args))
                    chatInfo.addMsg(chat_service.Msg(msg=json.dumps({"name":tool_call_name,"arguments":call["arguments"]},ensure_ascii=False),role=role,msg_type="function_call",id=call["id"]),trace=span)
                    call_result = available_functions[tool_call_name]["func"](app,user_id,chat_id = chatId,**call_args)
                    chatInfo.addMsg(chat_service.Msg(msg=call_result,role="function",msg_type=tool_call_name,id=call["id"]),trace=span)
                    call_span.update(output=call_result)
                    call_span.end()
            else:
                chatInfo.addMsg(
                chat_service.Msg(
                msg = text,
                role= role,
                msg_type="text"
                ),trace=span)
                generator.end(
                    output=text
                )
                span.update(output=text,input=reqtext,metadata={"user_id":user_id,"chat_id":chatId})
                trace.update(output=text)
            span.end()
     
        if new_chat:
            # 更新标题
            chat_info_text = "给下面对话起一个总结性标题,不超过十个字,只返回标题,不用标点标识，用户:{} AI:{}".format(reqtext,text)
            title = ""
            title_span = trace.span(name="gpt-name-chat-title")
            generator = title_span.generation(name="web-assistant-title",model=model,   input={"messages":{"role":"user","messages":chat_info_text}})
            for msg in invokeChat(app,"gpt-3.5-turbo-1106",chat_info_text):
                title = title + msg
                data =  {
                        'type': 'title',
                        'text':  msg,
                        'created': chatInfo.created.strftime("%Y-%m-%d %H:%M:%S"),
                        'chat_id': chatId
                }
                msg =  'data: '+json.dumps(data,default=fmt)+'\n\n'
                yield msg
            generator.end(output=title)
            chatInfo.updateTitle(app,title)
        
    except Exception as e:
        app.logger.error(traceback.format_exc())
        app.logger.error("出错啦,请稍后重试{}".format(e.__traceback__))
        msg =  'data: {"type":"content","text":"出错啦,请稍后重试,%s","chat_id":"%s"}\n\n'%(e.__format__,chatId)
        app.logger.info("msg:"+msg)
        yield msg


def get_openai_messages(messages :list) -> list[ChatCompletionMessageParam]:
    openai_messages = []
    for msg in messages:
        if msg['role'] == "user":
            openai_message = ChatCompletionUserMessageParam(**msg)
        elif msg['role'] == "assistant":
            openai_message = ChatCompletionAssistantMessageParam(**msg)
        elif msg['role'] == "system":
            openai_message = ChatCompletionSystemMessageParam(**msg)
        elif msg['role'] == "tool":
            openai_message = ChatCompletionToolMessageParam(**msg)
        openai_messages.append(openai_message)
    return openai_messages
def get_openai_tools(tools :list) -> list[ChatCompletionToolParam]:
    openai_tools = []

    for tool in tools:
        openai_tool = ChatCompletionToolParam(**tool)
        openai_tools.append(openai_tool)
    print(openai_tools)
    return openai_tools