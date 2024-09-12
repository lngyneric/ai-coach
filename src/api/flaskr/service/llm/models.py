from sqlalchemy import Column, String, Integer, TIMESTAMP, Text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.sql import func
from ...dao import db


class LLMEndpoint(db.Model):
    __tablename__ = "llm_endpoint"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    endpoint_name = Column(
        String(255), nullable=False, default="", comment="Endpoint name"
    )
    endpoint_url = Column(
        String(255), nullable=False, default="", comment="Endpoint URL"
    )
    endpoint_type = Column(Integer, nullable=False, default=0, comment="Endpoint type")
    endpoint_key = Column(
        String(255), nullable=False, default="", comment="Endpoint key"
    )
    endpoint_status = Column(
        Integer, nullable=False, default=0, comment="Endpoint status"
    )
    created_user_id = Column(
        String(255), nullable=False, default="", comment="Created user ID"
    )
    updated_user_id = Column(
        String(255), nullable=False, default="", comment="Updated user ID"
    )
    endpoint_created = Column(
        TIMESTAMP, nullable=False, default=func.now(), comment="Endpoint created"
    )
    endpoint_updated = Column(
        TIMESTAMP,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="Endpoint updated",
    )


class LLMModel(db.Model):
    __tablename__ = "llm_model"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    model_name = Column(String(255), nullable=False, default="", comment="Model name")
    model_type = Column(String(255), nullable=False, default="", comment="Model type")
    model_desc = Column(Text, nullable=False, comment="Model description")
    model_status = Column(Integer, nullable=False, default=0, comment="Model status")
    created_user_id = Column(
        String(255), nullable=False, default="", comment="Created user ID"
    )
    updated_user_id = Column(
        String(255), nullable=False, default="", comment="Updated user ID"
    )
    model_created = Column(
        TIMESTAMP, nullable=False, default=func.now(), comment="Model created"
    )
    model_updated = Column(
        TIMESTAMP,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="Model updated",
    )


class LLMGeneration(db.Model):
    __tablename__ = "llm_generation"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    model_name = Column(String(255), nullable=False, default="", comment="Model name")
    endpoint_name = Column(
        String(255), nullable=False, default="", comment="Endpoint name"
    )
    generation_model = Column(
        String(255), nullable=False, default="", comment="Generation model"
    )
    generation_type = Column(
        Integer, nullable=False, default=0, comment="Generation type"
    )
    generation_input = Column(Text, nullable=False, comment="Generation prompt")
    generation_output = Column(Text, nullable=False, comment="Generation output")
    generation_input_tokens = Column(
        Integer, nullable=False, default=0, comment="Generation input tokens"
    )
    generation_output_tokens = Column(
        Integer, nullable=False, default=0, comment="Generation output tokens"
    )
    generation_time_cost = Column(
        Integer, nullable=False, default=0, comment="Generation time cost"
    )
    course_id = Column(String(255), nullable=False, default="", comment="Course ID")
    lesson_id = Column(String(255), nullable=False, default="", comment="Lesson ID")
    script_id = Column(String(255), nullable=False, default="", comment="Script ID")
    user_id = Column(String(255), nullable=False, default="", comment="User ID")
    generation_created = Column(
        TIMESTAMP, nullable=False, default=func.now(), comment="Generation created"
    )
    generation_updated = Column(
        TIMESTAMP,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="Generation updated",
    )
