# backend/app/__init__.py
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

# 修正导入：从 search.py 导入 search_bp
from app.api.search import search_bp
from app.api.predict import predict_bp
from app.api.recommend import recommend_bp
from app.api.splice import splice_bp
from app.api.destinations import destinations_bp


def create_app():
    app = Flask(__name__)

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

    # 修正注册：使用正确的变量名
    app.register_blueprint(search_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(recommend_bp)
    app.register_blueprint(splice_bp)
    app.register_blueprint(destinations_bp)

    return app