# 机票智能搜索与推荐系统

## 项目简介
基于大数据和AI技术的智能机票搜索平台，整合各航空公司、航空联盟及OTA资源。

## 技术栈
- 大数据：Hadoop 3.4.3 / Hive 3.1.3 / Spark 3.5.3
- 数据库：Elasticsearch 7.x / Redis
- 后端：Flask + flasgger
- 前端：React + ECharts

## 开发环境
- Python 3.10+
- Node.js 18+
- Git

## 团队分工
| 角色    | 职责 | 负责目录 |
|-------|------|----------|
| 组长李舜乾 | 架构+数据工程+模型集成 | backend/ + data_engineering/ |
| 组员寸键熙 | ETL+数据清洗 | data_engineering/ |
| 组员徐浩轩 | 算法+模型 | algorithm/ |
| 组员袁思涵 | 后端API | backend/app/api/ |
| 组员张晓霞 | 前端+可视化 | frontend/ |

## 快速启动
```bash
# 后端
cd backend
pip install -r requirements.txt
python run.py

# 访问 http://localhost:5000/apidocs