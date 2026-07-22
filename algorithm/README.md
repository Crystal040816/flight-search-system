 Algorithm 模块

## 模块说明

本模块包含机票智能搜索系统的核心算法：

- **价格预测模型**：使用 XGBoost 预测机票价格
- **推荐引擎**：多因素综合评分推荐航班
- **拼接引擎**：多段航班组合搜索

## 文件结构
algorithm/
├── src/
│ ├── init.py # 模块入口
│ ├── model_loader.py # 统一模型加载器
│ ├── price_predictor.py # 价格预测训练脚本
│ ├── recommend_engine.py # 推荐引擎
│ ├── route_splicer.py # 拼接引擎
│ └── data_loader.py # 数据加载
├── models/
│ ├── price_predict_model.pkl
│ ├── encoders.pkl
│ ├── recommend_model.pkl
│ └── splice_model.pkl
└── README.md