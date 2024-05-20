import os

import yaml
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
# from langchain_wenxin import ChatWenxin
from langchain_community.chat_models import QianfanChatEndpoint

from config_manager import ConfigManager

_ = load_dotenv(find_dotenv())

cfg = ConfigManager()


def load_llm(model: str = None):
    if model is None:
        model = cfg.DEFAULT_MODEL

    if model in cfg.WENXIN_MODELS:
        return QianfanChatEndpoint(streaming=True, model=model)
    elif model in cfg.OPENAI_MODELS:
        return ChatOpenAI(model=model, organization=cfg.OPENAI_ORG)
