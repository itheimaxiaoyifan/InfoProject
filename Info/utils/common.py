"""
    写一些工具函数供使用
"""

# 过滤器名字to_class_name
from functools import wraps

from flask import session, current_app, g

from Info.models import User


def to_class_index(num):
    if num == 1:
        return 'first'
    elif num == 2:
        return 'second'
    elif num == 3:
        return 'third'
    else:
        return ""


def get_login_data(func):  # 装饰器获取用户登录信息
    @wraps(func)
    def inner(*args, **kwargs):
        user_id = session.get('user_id')
        # 2.通过id获取用户信息
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
        g.user = user
        return func(*args, **kwargs)

    return inner
