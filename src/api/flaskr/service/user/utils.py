from flask import Flask
import jwt
import time
import base64
import string
import random

from ..common.models import CHECK_CODE_ERROR, CHECK_CODE_EXPIRED
from ...dao import db,redis_client as redis
from captcha.image import ImageCaptcha 
from ...api.aliyun import send_sms_code_ali
from io import BytesIO




# generate token
def generate_token(app:Flask, user_id: str) -> str:
    with app.app_context():
        token = jwt.encode({'user_id': user_id,"time_stamp": time.time()}, app.config['SECRET_KEY'], algorithm='HS256')
        redis.set(app.config["REDIS_KEY_PRRFIX_USER"] + user_id, token,ex=app.config['TOKEN_EXPIRE_TIME'])
        return token
    
 



# generate image captcha
# author: yfge
def generation_img_chk(app:Flask,mobile:str):
    with app.app_context():
        image_captcha = ImageCaptcha()
        characters = string.ascii_uppercase + string.digits
        # Generate a random string of length 4
        random_string = ''.join(random.choices(characters, k=4))
        captcha_image = image_captcha.generate_image(random_string)
        # Save the image to a BytesIO object
        buffered = BytesIO()
        captcha_image.save(buffered, format="PNG")
        app.logger.info("mobile:"+mobile+" random_string:"+random_string)
        # Encode the image to base64
        img_base64 = 'data:image/png;base64,'+base64.b64encode(buffered.getvalue()).decode('utf-8')
        redis.set(app.config["REDIS_KEY_PRRFIX_CAPTCHA"] + mobile, random_string,ex=app.config['CAPTCHA_CODE_EXPIRE_TIME'])
        return {
            "img":img_base64,
            "expire_in":app.config['CAPTCHA_CODE_EXPIRE_TIME']
        }

# send sms code
# author: yfge 
def send_sms_code_without_check(app:Flask,user_id:str,phone:str,User)->str:
    user = User.query.filter(User.user_id==user_id).first()
    user.mobile = phone
    characters =  string.digits
    random_string = ''.join(random.choices(characters, k=4))
    # 发送短信验证码
    redis.set(app.config["REDIS_KEY_PRRFIX_PHONE"]+user_id,phone,ex=app.config.get("PHONE_EXPIRE_TIME",60*30))
    redis.set(app.config["REDIS_KEY_PRRFIX_PHONE_CODE"] + phone, random_string,ex=app.config['PHONE_CODE_EXPIRE_TIME'])
    send_sms_code_ali(app,phone,random_string)
    db.session.flush()
    return {
        "expire_in":app.config['PHONE_CODE_EXPIRE_TIME'],
        "phone":phone
    }




# send sms code
def send_sms_code(app:Flask,phone:str,chekcode:str):
    with app.app_context():
        check_save = redis.get(app.config["REDIS_KEY_PRRFIX_CAPTCHA"] + phone)
        if check_save == None:
            raise CHECK_CODE_EXPIRED
        check_save_str = str(check_save,encoding="utf-8") 
        app.logger.info("check_save_str:"+check_save_str+" chekcode:"+chekcode)
        if chekcode.lower() != check_save_str.lower():
            raise CHECK_CODE_ERROR
        else:
            characters =  string.digits
            # Generate a random string of length 4
            random_string = ''.join(random.choices(characters, k=4))
            # 发送短信验证码
            redis.set(app.config["REDIS_KEY_PRRFIX_PHONE_CODE"] + phone, random_string,ex=app.config['PHONE_CODE_EXPIRE_TIME'])
            send_sms_code_ali(app,phone,random_string)
            return {
                "expire_in":app.config['PHONE_CODE_EXPIRE_TIME']
            } 