# backend/app/config.py
import os

ES_HOST = '192.168.128.27'
ES_PORT = 9200
REDIS_HOST = '192.168.128.27'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None


def env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'flight-search-secret-key-12345'

    # Elasticsearch 连接配置
    ELASTICSEARCH_HOST = os.environ.get('ES_HOST') or ES_HOST
    ELASTICSEARCH_PORT = int(os.environ.get('ES_PORT') or ES_PORT)

    # Redis 连接配置
    REDIS_HOST = os.environ.get('REDIS_HOST') or REDIS_HOST
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or REDIS_PORT)
    REDIS_DB = int(os.environ.get('REDIS_DB') or REDIS_DB)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD') or REDIS_PASSWORD

    # 新增：MySQL ADS 业务层配置 (通过本地转发端口 13306 访问，密码填写组长/数据同学给您的真实密码)
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or '127.0.0.1'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'flight_ads'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'flight_ads_reader'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or '123456'

    SPLICE_SEARCH_DATE = os.environ.get('SPLICE_SEARCH_DATE') or '2022-04-19'
    SPLICE_REDIS_ENABLED = env_flag('SPLICE_REDIS_ENABLED', False)
    EXTERNAL_SERVICE_TIMEOUT_SECONDS = float(
        os.environ.get('EXTERNAL_SERVICE_TIMEOUT_SECONDS') or 1.0
    )
