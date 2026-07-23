# backend/app/api/predict.py
from flask import Blueprint, request
from app.models.response import UnifiedResponse
from app.services.predict_service import price_predict_service

predict_bp = Blueprint('predict', __name__, url_prefix='/api')


@predict_bp.route('/predict', methods=['POST'])
def predict_price():
    """
    高级价格趋势预测接口 (已对接物理 XGBoost 与 Encoders)
    ---
    tags:
      - 预测
    summary: 预测搜索日到起飞日之间的每日机票价格走势
    description: 输入出发机场、目的地机场、起飞日期，自动计算天数并调起物理 price_predict_model.pkl 执行每日价格推演。返回统计、低价购买建议。
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - departure
            - destination
            - flightDate
          properties:
            departure:
              type: string
              description: 出发地机场 IATA 三字码
              example: "LGA"
            destination:
              type: string
              description: 目的地机场 IATA 三字码
              example: "SFO"
            flightDate:
              type: string
              format: date
              description: 目标起飞日期 (2022-04-20 至 2022-06-21)
              example: "2022-06-08"
            days:
              type: integer
              description: 需要推演的价格趋势天数
              default: 7
              example: 7
    responses:
      200:
        description: 成功返回高维度价格走势分析数据
    """
    try:
        data = request.get_json()
        if not data:
            return UnifiedResponse.bad_request("请求体不能为空")

        required = ['departure', 'destination', 'flightDate']
        for field in required:
            if field not in data:
                return UnifiedResponse.bad_request(f"缺少必填参数: {field}")

        departure = data.get('departure')
        destination = data.get('destination')
        flight_date = data.get('flightDate')
        days = data.get('days', 7)

        # 调起全新重构的预测服务
        result = price_predict_service.predict_price_trend(
            origin=departure,
            destination=destination,
            departure_date=flight_date,
            days=days
        )

        return UnifiedResponse.success(result)

    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")