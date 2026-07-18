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

    # Elasticsearch 连接配置 (假定 ES 部署在 node-master 节点)
    ELASTICSEARCH_HOST = os.environ.get('ES_HOST')
    ELASTICSEARCH_PORT = int(os.environ.get('ES_PORT'))

    # Redis 连接配置 (假定 Redis 部署在 node-master 节点)
    REDIS_HOST = os.environ.get('REDIS_HOST')
    REDIS_PORT = int(os.environ.get('REDIS_PORT'))
    REDIS_DB = int(os.environ.get('REDIS_DB') )
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')