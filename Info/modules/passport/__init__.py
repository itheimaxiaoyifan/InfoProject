"""
    主要负责写关于注册时候图片验证以及短信验证的代码
"""
from flask import Blueprint
passport_blu = Blueprint('passport', __name__, url_prefix='/passport')
from . import views