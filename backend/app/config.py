# backend/app/config.py
import os

ES_HOST = '192.168.128.27'
ES_PORT = 9200
REDIS_HOST = '192.168.128.27'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

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
    MYSQL_HOST = '127.0.0.1'
    MYSQL_PORT = 3306
    MYSQL_DB = 'flight_ads'
    MYSQL_USER = 'flight_ads_reader'
    MYSQL_PASSWORD = '123456'