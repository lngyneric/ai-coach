# import logging
# from dotenv import load_dotenv
# # from openai import OpenAI
# # from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.prompts import PromptTemplate
# from langchain_core.messages.ai import AIMessage
# # from langchain_openai import ChatOpenAI
# from langchain_openai import OpenAI

# from prompt.agent import *


# # model = ChatOpenAI(
# #     model='gpt-4'
# # )

# llm = OpenAI(model='gpt-4')

# # load_dotenv()

# # # 初始化OpenAI
# # client = OpenAI()


# # # 检查用户昵称是否合法
# # def check_nickname(nickname: str) -> AIMessage:
# #     prompt = ChatPromptTemplate.from_template(CHECK_NICKNAME)
# #     chain = prompt | model
# #     result = chain.invoke({"nickname": nickname})
# #     print(result)
# #     return result
    
    
# # 检查用户昵称是否合法
# # async def check_nickname(nickname: str) -> AIMessage:
# #     prompt = PromptTemplate(CHECK_NICKNAME, input_variables=["nickname"])
# #     chunks = []
# #     async for chunk in llm.astream(prompt.format(nickname=nickname)):
# #         chunks.append(chunk)
# #         print(chunk.content, end='|', flush=True)
    
        
# def check_nickname(nickname: str):
#     full_result = ''
#     for chunk in llm.stream(prompt.format(nickname=nickname)):
#         full_result += chunk.content
#         if logging.getLogger().level == logging.DEBUG:
#             print(chunk.content, end='', flush=True)
#     logging.debug(f'check_nickname: {full_result}')
    

    