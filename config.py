import redis


class Config(object):
    # 配置mysql数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://xyf:123456@127.0.0.1:13306/info_gz08'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 配置Redis
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    # 配置session
    SECRET_KEY = '@#!%$%%$^%$^#$#$@#$!!@$$%^!'
    SESSION_TYPE = 'redis'
    SESSION_SESSION_LIFETIME = 3600 * 24 * 2
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    # CSRF防护配置


# 开发环境的配置
class DevelopConfig(Config):
    DEBUG = True


# 生产环境的配置
class ProductionConfig(Config):
    DEBUG = False


ConfigDict = {'develop': DevelopConfig, 'product': ProductionConfig}
