from ...api.llm import invoke_llm
from .models import LLMGeneration  # , LLMEndpoint, LLMModel
from flask import Flask

from langfuse.client import StatefulSpanClient


def invoke_llm_api(
    app: Flask,
    user_id: str,
    course_id: str,
    lesson_id: str,
    script_id: str,
    span: StatefulSpanClient,
    model: str,
    message: str,
    system: str = None,
    json: bool = False,
    **kwargs
):
    generation = LLMGeneration()
    generation.course_id = course_id
    generation.lesson_id = lesson_id
    generation.user_id = user_id
    generation.script_id = script_id
    generation.model_name = model
    generation.generation_input = message

    yield from invoke_llm(app, span, model, message, system, json, kwargs)
