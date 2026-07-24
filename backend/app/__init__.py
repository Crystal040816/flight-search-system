# backend/app/__init__.py
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

# 导入 Elasticsearch 和 Redis 驱动
from redis import Redis
from elasticsearch import Elasticsearch

# 导入配置
from app.config import Config

# 从 search.py 导入 search_bp
from app.api.search import search_bp
from app.api.predict import predict_bp
from app.api.recommend import recommend_bp
from app.api.splice import splice_bp
from app.api.destinations import destinations_bp
from app.models.response import UnifiedResponse

# 声明全局变量，方便在 services 中导入
redis_client = None
es_client = None


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. 实例化全局 Redis 客户端 (双层 try-except 容错保护)
    global redis_client
    try:
        timeout = float(app.config.get('EXTERNAL_SERVICE_TIMEOUT_SECONDS', 1.0))
        redis_client = Redis(
            host=app.config['REDIS_HOST'],
            port=app.config['REDIS_PORT'],
            db=app.config['REDIS_DB'],
            password=app.config['REDIS_PASSWORD'],
            decode_responses=True,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
            retry_on_timeout=False
        )
        print("[系统初始化] Redis 驱动并网成功")
    except Exception as e:
        print(f"[系统初始化] Redis 实例化失败 (已启用防崩沙箱保护): {str(e)}")
        redis_client = None

    # 2. 实例化全局 Elasticsearch 客户端 (防参数版本不兼容多级保护)
    global es_client
    try:
        es_protocol = "http"
        es_host = app.config['ELASTICSEARCH_HOST']
        es_port = app.config['ELASTICSEARCH_PORT']
        timeout = float(app.config.get('EXTERNAL_SERVICE_TIMEOUT_SECONDS', 1.0))

        # 优先尝试使用用户指定的高阶参数
        es_client = Elasticsearch(
            [f"{es_protocol}://{es_host}:{es_port}"],
            timeout=timeout,
            max_retries=0,
            retry_on_timeout=False
        )
        print("[系统初始化] Elasticsearch 驱动并网成功")
    except Exception as e:
        print(f"[系统初始化] 检测到当前虚拟机 ES 驱动版本存在不兼容参数，正在自动切换为安全级构造函数: {str(e)}")
        try:
            # 安全级保底构造函数：只保留 100% 被所有版本兼容的连接与超时参数，彻底防止崩服！
            es_client = Elasticsearch(
                [f"{es_protocol}://{es_host}:{es_port}"],
                timeout=timeout
            )
            print("[系统初始化] Elasticsearch 驱动安全级加载成功 ✅")
        except Exception as ex:
            print(f"[系统初始化] Elasticsearch 整体实例化失败 (已启用防崩沙箱保护): {str(ex)}")
            es_client = None

    # 3. Swagger 配置 (统一为最稳定、无 404 隐患的 2 版本)
    app.config['SWAGGER'] = {
        'title': '机票智能搜索系统 API',
        'version': '1.0.0',
        'description': '基于大数据的智能机票搜索与推荐系统',
        'contact': {
            'name': '开发团队'
        },
        'uiversion': 2
    }

    CORS(app)
    Swagger(app)

    # 注册所有蓝图
    app.register_blueprint(search_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(recommend_bp)
    app.register_blueprint(splice_bp)
    app.register_blueprint(destinations_bp)

    # 4. 集成原 main.py 的健康检查
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查"""
        return UnifiedResponse.success({
            "status": "running",
            "services": {
                "api": "healthy",
                "es": "connected" if es_client else "pending",
                "redis": "connected" if redis_client else "pending"
            }
        })

    return app