import redis
from flask import Flask, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from config import ConfigDict


def create_app(env):
    app = Flask(__name__)
    # 给APP添加配置信息
    current_app_config = ConfigDict[env]
    app.config.from_object(current_app_config)
    db = SQLAlchemy(app)
    Redis_sto = redis.StrictRedis(host=current_app_config.REDIS_HOST, port=current_app_config.REDIS_PORT)
    Session(app)
    return app
