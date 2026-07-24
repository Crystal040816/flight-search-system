# backend/app/__init__.py
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

# 导入 Elasticsearch 和 Redis 驱动
from redis import Redis
from elasticsearch import Elasticsearch

# 导入我们之前写的 Config 配置
from app.config import Config

# 从 search.py 导入 search_bp
from app.api.search import search_bp
from app.api.predict import predict_bp
from app.api.recommend import recommend_bp
from app.api.splice import splice_bp
from app.api.destinations import destinations_bp

# 声明全局变量，方便在 services 中导入
redis_client = None
es_client = None


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. 实例化全局 Redis 客户端
    global redis_client
    redis_client = Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB'],
        password=app.config['REDIS_PASSWORD'],
        decode_responses=True
    )

    # 2. 实例化全局 Elasticsearch 客户端
    global es_client
    es_protocol = "http"
    es_host = app.config['ELASTICSEARCH_HOST']
    es_port = app.config['ELASTICSEARCH_PORT']
    es_client = Elasticsearch([f"{es_protocol}://{es_host}:{es_port}"])

    # Swagger 配置
    app.config['SWAGGER'] = {
        'title': '机票智能搜索系统 API',
        'version': '1.0.0',
        'description': '基于大数据的智能机票搜索与推荐系统',
        'contact': {
            'name': '开发团队'
        },
        'uiversion': 3
    }

    CORS(app)
    Swagger(app)

    # 注册所有蓝图
    app.register_blueprint(search_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(recommend_bp)
    app.register_blueprint(splice_bp)
    app.register_blueprint(destinations_bp)

    return app