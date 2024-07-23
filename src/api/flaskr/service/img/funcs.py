from .models import Image
from flask import Flask

from ...dao import db
def add_image(app:Flask, img_id, chat_id, user_id, bucket_id, prompt, size, url, bucket_base):
    with app.app_context():
        session = db.session
        image = Image(
            img_id=img_id,
            chat_id=chat_id,
            user_id=user_id,
            bucket_id=bucket_id,
            prompt=prompt,
            size=size,
            url=url,
            bucket_base=bucket_base
        )
        session.add(image)
        session.commit()
        return image.id
