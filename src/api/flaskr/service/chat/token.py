from typing import List, Optional, Union, Dict, Any
from flask import Flask
# Assuming you have equivalent Python modules for OpenAI, Tiktoken, and functions
# import OpenAI
import tiktoken
# import functions
encoder = tiktoken.get_encoding("cl100k_base")
def prompt_tokens_estimate(app:Flask,messages: List, functions: Optional[List] = None) -> int:
    padded_system = False
    tokens = sum([
        message_tokens_estimate(m) if not (m["role"] == "system" and functions and not padded_system) else message_tokens_estimate({**m, "content": m["content"] + "\n"}) for m in messages
    ])
    tokens += 3
    app.logger.info("message tokens: {}".format(tokens))
    if functions:
        tokens += functions_tokens_estimate(app,functions)
    if functions and any(m.get('role','') == "system" for m in messages):
        tokens -= 4
    return tokens


def string_tokens(s: str) -> int:
    global encoder
    return len(encoder.encode(s))


def message_tokens_estimate(message) -> int:
    components = [
        comp for comp in [message["role"], message["content"], message.get('name',''), message.get("function_call", {}).get("name"), getattr(message, "function_call", {}).get("arguments")] if comp
    ]
    tokens = sum([string_tokens(comp) for comp in components])
    tokens += 3
    if message.get("name",None):
        tokens += 1
    if message.get("role",None) == "function":
        tokens -= 2
    if message.get("function_call",None):
        tokens += 3
    return tokens

def functions_tokens_estimate(app:Flask,funcs: List) -> int:
    prompt_definitions = format_function_definitions(funcs)
    app.logger.info("function definitions: {}".format(prompt_definitions))
    tokens = string_tokens(prompt_definitions)
    tokens += 9  # Add nine per completion
    app.logger.info('function tokens: {}'.format(tokens))
    return tokens
def format_function_definitions(funcs: List) -> str:
    return ", ".join([str(f) for f in funcs])  # Dummy implementation
