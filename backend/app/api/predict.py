# backend/app/api/predict.py
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from app.models.request import PredictRequest
from app.models.response import UnifiedResponse
from app.services import predict_service
from app.services.predict_service import price_predict_service

predict_bp = Blueprint('predict', __name__, url_prefix='/api')


@predict_bp.route('/predict', methods=['POST'])
def predict_price():
    """
    价格预测接口
    ---
    tags:
      - 预测
    summary: 预测未来机票价格
    description: 输入出发地、目的地、日期，返回预测价格和最佳购票时间
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
              description: 出发地 IATA 三字码
              example: PEK
            destination:
              type: string
              description: 目的地 IATA 三字码
              example: PVG
            flightDate:
              type: string
              format: date
              description: 目标日期
              example: "2026-08-01"
    responses:
      200:
        description: 成功
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            data:
              type: object
              properties:
                predictedPrice:
                  type: number
                  example: 850
                bestTimeToBuy:
                  type: string
                  example: "2026-07-10"
    """
    try:
        data = request.get_json()
        if not data:
            return UnifiedResponse.bad_request("请求体不能为空")

        required = ['departure', 'destination', 'flightDate']
        for field in required:
            if field not in data:
                return UnifiedResponse.bad_request(f"缺少必填参数: {field}")

        # TODO: 组员B提供价格预测模型
        departure = data.get('departure')
        destination = data.get('destination')
        flight_date = data.get('flightDate')

        # 调用服务层：内部已集成 Redis 缓存与组员B的机器学习模型
        result = price_predict_service.predict_price_trend(departure, destination, flight_date)

        return UnifiedResponse.success(result)
        # 当前返回 Mock 数据
        # mock_data = {
        #     "departure": data.get('departure', 'PEK'),
        #     "destination": data.get('destination', 'PVG'),
        #     "flightDate": data.get('flightDate'),
        #     "predictedPrice": qq850,
        #     "currency": "CNY",
        #     "confidence_lower": 780,
        #     "confidence_upper": 920,
        #     "bestTimeToBuy": "2026-07-10"
        # }
        #
        # return UnifiedResponse.success(mock_data)

    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")