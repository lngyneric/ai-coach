import os

import yaml
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
# from langchain_wenxin import ChatWenxin
from langchain_community.chat_models import QianfanChatEndpoint, ChatZhipuAI

from config_manager import ConfigManager

_ = load_dotenv(find_dotenv())

cfg = ConfigManager()


def load_llm(model: str = None, temperature: float = None):
    model = cfg.DEFAULT_MODEL if model is None else model
    if model in cfg.QIANFAN_MODELS:
        temperature = temperature if temperature else cfg.QIANFAN_DEF_TMP
        return QianfanChatEndpoint(streaming=True, model=model, temperature=temperature)
    elif model in cfg.ZHIPU_MODELS:
        temperature = temperature if temperature else cfg.ZHIPU_DEF_TMP
        return ChatZhipuAI(streaming=True, model=model, temperature=temperature)
    elif model in cfg.OPENAI_MODELS:
        temperature = temperature if temperature else cfg.OPENAI_DEF_TMP
        return ChatOpenAI(model=model, temperature=temperature, organization=cfg.OPENAI_ORG)
    else:
        raise Exception('模型名称错误（不支持）')
