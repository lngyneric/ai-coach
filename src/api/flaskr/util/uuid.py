from flask import Flask
import uuid


# generate a uuid
def generate_id(app: Flask) -> str:
    return str(uuid.uuid4()).replace("-", "")
