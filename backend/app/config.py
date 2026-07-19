# backend/app/config.py
import os

# 1. 这里是您的全局默认配置 (当系统环境变量不存在时，将作为备用值)
ES_HOST = '192.168.128.27'
ES_PORT = 9200
REDIS_HOST = '192.168.128.27'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'flight-search-secret-key-12345'

    # 2. 对齐逻辑：若读取不到系统环境变量，则使用上方的全局默认配置
    ELASTICSEARCH_HOST = os.environ.get('ES_HOST') or ES_HOST
    ELASTICSEARCH_PORT = int(os.environ.get('ES_PORT') or ES_PORT)

    # 3. 对齐逻辑：若读取不到系统环境变量，则使用上方的全局默认配置
    REDIS_HOST = os.environ.get('REDIS_HOST') or REDIS_HOST
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or REDIS_PORT)
    REDIS_DB = int(os.environ.get('REDIS_DB') or REDIS_DB)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD') or REDIS_PASSWORD