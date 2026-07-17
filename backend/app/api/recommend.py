# backend/app/api/recommend.py
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from app.models.request import RecommendRequest
from app.models.response import UnifiedResponse
from app.models.flight import Flight

recommend_bp = Blueprint('recommend', __name__, url_prefix='/api')


@recommend_bp.route('/recommend', methods=['POST'])
def recommend():
    """
    智能推荐接口
    ---
    tags:
      - 推荐
    summary: 基于多因素推荐最佳航班
    description: 考虑价格、时长、中转次数、机型、航空公司等因素综合评分
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
              example: PEK
            destination:
              type: string
              example: PVG
            flightDate:
              type: string
              format: date
              example: "2026-07-20"
            preferences:
              type: object
              properties:
                preferLowPrice:
                  type: boolean
                  description: 是否偏好低价
                preferShortDuration:
                  type: boolean
                  description: 是否偏好短时长
                preferDirect:
                  type: boolean
                  description: 是否偏好直飞
    responses:
      200:
        description: 成功
    """
    try:
        data = request.get_json()
        if not data:
            return UnifiedResponse.bad_request("请求体不能为空")

        required = ['departure', 'destination', 'flightDate']
        for field in required:
            if field not in data:
                return UnifiedResponse.bad_request(f"缺少必填参数: {field}")

        # TODO: 组员B提供推荐算法
        # 当前返回 Mock 数据
        mock_recommendations = [
            {
                "rank": 1,
                "reason": "价格最低，性价比最高",
                "flight": Flight(
                    flightNumber="CA1234",
                    departureTime=f"{data.get('flightDate')} 08:00",
                    arrivalTime=f"{data.get('flightDate')} 10:30",
                    duration="2h30m",
                    stops=0,
                    airline="中国国航",
                    airlineCode="CA",
                    price=1200
                ).to_dict()
            },
            {
                "rank": 2,
                "reason": "总时长最短，直飞无中转",
                "flight": Flight(
                    flightNumber="MU5678",
                    departureTime=f"{data.get('flightDate')} 07:00",
                    arrivalTime=f"{data.get('flightDate')} 09:00",
                    duration="2h0m",
                    stops=0,
                    airline="东方航空",
                    airlineCode="MU",
                    price=1500
                ).to_dict()
            }
        ]

        return UnifiedResponse.success({
            "recommendations": mock_recommendations,
            "total": len(mock_recommendations)
        })

    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")