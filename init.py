import os

import yaml
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
# from langchain_wenxin import ChatWenxin
from langchain_community.chat_models import QianfanChatEndpoint

from config_manager import ConfigManager

_ = load_dotenv(find_dotenv())

cfg = ConfigManager()


def load_llm(model: str = cfg.DEFAULT_MODEL, temperature: float = None):
    if model in cfg.QIANFAN_MODELS:
        temperature = temperature if temperature else cfg.QIANFAN_DEF_TMP
        return QianfanChatEndpoint(streaming=True, model=model, temperature=temperature, verbose=True)
    elif model in cfg.OPENAI_MODELS:
        temperature = temperature if temperature else cfg.OPENAI_DEF_TMP
        return ChatOpenAI(model=model, temperature=temperature, organization=cfg.OPENAI_ORG)
