# backend/app/__init__.py
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger


def create_app():
    app = Flask(__name__)
    app.config['SWAGGER'] = {
        'title': '机票智能搜索系统 API',
        'version': '1.0.0',
        'description': '基于大数据的智能机票搜索与推荐系统',
        'contact': {'name': '开发团队'},
        'uiversion': 3
    }

    CORS(app)
    Swagger(app)

    # 注册蓝图
    from app.api import search
    app.register_blueprint(search.bp)

    return app