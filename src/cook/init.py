import os

import yaml
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
# from langchain_wenxin import ChatWenxin
from langchain_community.chat_models import QianfanChatEndpoint, ChatZhipuAI

from config_manager import ConfigManager

_ = load_dotenv(find_dotenv())

cfg = ConfigManager()


def load_llm(model: str = None, temperature: float = None, json_mode=False):
    model = cfg.DEFAULT_MODEL if model is None else model
    if model in cfg.QIANFAN_MODELS:
        temperature = temperature if temperature else cfg.QIANFAN_DEF_TMP
        if json_mode:
            return QianfanChatEndpoint(streaming=True, model=model, temperature=temperature,
                                       model_kwargs={"response_format": "json_object"})
        else:
            return QianfanChatEndpoint(streaming=True, model=model, temperature=temperature)
    elif model in cfg.ZHIPU_MODELS:
        temperature = temperature if temperature else cfg.ZHIPU_DEF_TMP
        if json_mode:
            raise Exception('ZhipuAI 暂不支持 JSON 模式')
        else:
            return ChatZhipuAI(streaming=True, model=model, temperature=temperature)
    elif model in cfg.OPENAI_MODELS:
        temperature = temperature if temperature else cfg.OPENAI_DEF_TMP
        if json_mode:
            return ChatOpenAI(model=model, temperature=temperature, organization=cfg.OPENAI_ORG,
                              model_kwargs={"response_format": {"type": "json_object"}})
        else:
            return ChatOpenAI(model=model, temperature=temperature, organization=cfg.OPENAI_ORG)
    else:
        raise Exception('模型名称错误（不支持）')
