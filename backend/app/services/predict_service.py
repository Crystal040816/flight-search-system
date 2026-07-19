# backend/app/services/predict_service.py
import os
import json
import joblib  # 用于加载算法同学的 pkl 模型
from datetime import datetime, timedelta

# 尝试导入全局 Redis 客户端（兼容两种启动模式下的导入路径）
try:
    from backend.app import redis_client
except ImportError:
    try:
        from app import redis_client
    except ImportError:
        redis_client = None


class PricePredictService:
    def __init__(self):
        # 确定模型存放路径
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        self.model_path = os.path.join(base_dir, "algorithm", "models", "price_predictor.pkl")
        self.model = None

        # 尝试加载组员 B 的模型
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print(f"[Predict Service] 成功加载算法模型: {self.model_path}")
            except Exception as e:
                print(f"[Predict Service] 模型加载失败，启用降级算法。原因: {str(e)}")
        else:
            print(f"[Predict Service] 模型文件未找到，启用降级算法。路径: {self.model_path}")

    def predict_price_trend(self, origin: str, destination: str, departure_date: str):
        """
        核心业务：预测未来7天的机票价格趋势
        """
        cache_key = f"predict:{origin}:{destination}:{departure_date}"

        # 1. 尝试从 Redis 读取缓存
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    print(f"[Redis Hit] 命中价格预测缓存: {cache_key}")
                    return json.loads(cached_data)
            except Exception as e:
                print(f"[Redis Error] 缓存读取异常: {str(e)}")

        # 2. 执行预测计算
        trend_data = []
        if self.model:
            try:
                # 如果模型存在，调用组员 B 的模型进行真实预测
                # 这里假设模型有一个 predict_days 的方法，或根据具体模型 API 传入特征
                # 实际联调时，根据组员 B 提供的预测接口进行微调
                trend_data = self.model.predict_days(origin, destination, departure_date, days=7)
            except Exception as e:
                print(f"[Model Error] 模型计算失败，转为规则计算: {str(e)}")
                trend_data = self._generate_fallback_trend(departure_date)
        else:
            # 模型未就绪时的平滑降级方案
            trend_data = self._generate_fallback_trend(departure_date)

        # 3. 组装返回结果
        result = {
            "origin": origin,
            "destination": destination,
            "start_date": departure_date,
            "trend": trend_data,
            "suggestion": "当前价格处于近期低位，建议购票。" if trend_data[0][
                                                                  "predicted_price"] < 550 else "预计价格将有上涨趋势，建议尽快购买。"
        }

        # 4. 写入 Redis 缓存
        if redis_client:
            try:
                redis_client.setex(cache_key, 3600, json.dumps(result, ensure_ascii=False))  # 缓存1小时
                print(f"[Redis Save] 价格预测结果写入缓存: {cache_key}")
            except Exception as e:
                print(f"[Redis Error] 缓存写入异常: {str(e)}")

        return result

    def _generate_fallback_trend(self, departure_date: str):
        """降级方案：根据输入日期模拟生成未来 7 天的走势数据"""
        try:
            base_date = datetime.strptime(departure_date, "%Y-%m-%d")
        except ValueError:
            base_date = datetime.today()

        mock_prices = [580, 520, 490, 510, 600, 620, 550]
        trend = []
        for i in range(7):
            curr_date = base_date + timedelta(days=i)
            trend.append({
                "date": curr_date.strftime("%Y-%m-%d"),
                "predicted_price": mock_prices[i]
            })
        return trend


# 实例化
predict_service = PricePredictService()