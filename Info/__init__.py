import logging
from logging.handlers import RotatingFileHandler

import redis
from flask import Flask, session, render_template, g
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

from config import ConfigDict

db = SQLAlchemy()
Redis_store = None


def create_app(env):
    app = Flask(__name__)
    # 给APP添加配置信息
    current_app_config = ConfigDict[env]
    app.config.from_object(current_app_config)
    # 配置日志信息
    # 调用记录日志函数
    log_file(current_app_config.LOG_LV)

    db.init_app(app)
    global Redis_store
    Redis_store = redis.StrictRedis(host=current_app_config.REDIS_HOST, port=current_app_config.REDIS_PORT)
    Session(app)

    # 添加csrf防护,验证前端与后端是否一致
    from flask_wtf import CSRFProtect
    CSRFProtect(app)

    from flask_wtf.csrf import generate_csrf
    @app.after_request
    def after_request(response):
        # 生成token
        csrf_token = generate_csrf()
        # 传给前端csrf值
        response.set_cookie('csrf_token', csrf_token)
        return response

    # 生成一个过滤器给前端去展示首页的点击排行页面
    from Info.utils.common import to_class_index
    app.add_template_filter(to_class_index, "to_class_name")
    # 注册蓝图
    from Info.modules.index import index_blu
    app.register_blueprint(index_blu)
    from Info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)
    from Info.modules.news_detail import news_detail_blu
    app.register_blueprint(news_detail_blu)
    from Info.modules.profile import profile_blu
    app.register_blueprint(profile_blu)
    from Info.modules.admin import admin_blu
    app.register_blueprint(admin_blu)

    from Info.utils.common import get_login_data
    @app.errorhandler(404)
    @get_login_data
    def page_not_found(_):
        user = g.user
        data = {
            "user_info": user.to_dict() if user else None,
        }
        return render_template('news/404.html',data=data )

    return app


def log_file(lv):
    """记录日志信息"""
    # 设置哪些日志信息等级要被记录
    logging.basicConfig(level=lv)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)
