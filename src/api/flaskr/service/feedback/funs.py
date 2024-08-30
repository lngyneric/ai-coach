from flask import Flask
from .models import FeedBack
from ...dao import db


def submit_feedback(app: Flask, user_id: str, feedback: str):
    with app.app_context():
        feedback = FeedBack(user_id=user_id, feedback=feedback)
        db.session.add(feedback)
        db.session.commit()
        return feedback.id
