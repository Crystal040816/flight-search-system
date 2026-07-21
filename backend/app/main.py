# backend/app/main.py
from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

# 从 api 包导入所有蓝图
from app.api import search_bp, predict_bp, recommend_bp, splice_bp, destinations_bp
from app.models.response import UnifiedResponse

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

# 注册所有蓝图
app.register_blueprint(search_bp)
app.register_blueprint(predict_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(splice_bp)
app.register_blueprint(destinations_bp)


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return UnifiedResponse.success({
        "status": "running",
        "services": {
            "api": "healthy",
            "es": "pending",
            "redis": "pending"
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)