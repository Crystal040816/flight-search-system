# backend/app/api/search.py
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from app.models.request import SearchRequest
from app.models.response import UnifiedResponse
from app.models.flight import Flight

search_bp = Blueprint('search', __name__, url_prefix='/api')


@search_bp.route('/search', methods=['POST'])
def search_flights():
    """
    航班搜索接口
    ---
    tags:
      - 搜索
    summary: 实时搜索航班
    description: 根据出发地、目的地、日期搜索航班，支持单程/往返/多程
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
              description: 出发日期
              example: "2026-07-20"
            tripType:
              type: string
              enum: [ONE_WAY, ROUND_TRIP, MULTI_CITY]
              description: 行程类型
              default: ONE_WAY
            returnDate:
              type: string
              format: date
              description: 返程日期（往返时必填）
            page:
              type: integer
              default: 1
            size:
              type: integer
              default: 20
            sortBy:
              type: string
              enum: [price, duration, departureTime]
              default: price
            filters:
              type: object
              properties:
                airlines:
                  type: array
                  items:
                    type: string
                  example: ["CA", "MU"]
                maxStops:
                  type: integer
                  example: 2
                minPrice:
                  type: number
                  example: 0
                maxPrice:
                  type: number
                  example: 10000
    responses:
      200:
        description: 成功
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            message:
              type: string
              example: success
            data:
              type: object
              properties:
                total:
                  type: integer
                  example: 156
                flights:
                  type: array
                  items:
                    type: object
                    properties:
                      flightNumber:
                        type: string
                        example: CA1234
                      price:
                        type: number
                        example: 1200
    """
    try:
        data = request.get_json()
        if not data:
            return UnifiedResponse.bad_request("请求体不能为空")

        required = ['departure', 'destination', 'flightDate']
        for field in required:
            if field not in data:
                return UnifiedResponse.bad_request(f"缺少必填参数: {field}")

        # TODO: 组员C后续替换为真实 ES 查询
        # 当前返回 Mock 数据
        mock_flights = _get_mock_flights(data)

        return UnifiedResponse.success({
            "total": len(mock_flights),
            "flights": [f.to_dict() for f in mock_flights]
        })

    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")


def _get_mock_flights(data: dict) -> list:
    """生成 Mock 数据"""
    departure = data.get('departure', 'PEK')
    destination = data.get('destination', 'PVG')
    flight_date = data.get('flightDate', '2026-07-20')

    mock_list = []
    for i in range(5):
        flight = Flight(
            flightNumber=f"CA{1000 + i}",
            departureTime=f"{flight_date} 08:{30 + i * 10:02d}",
            arrivalTime=f"{flight_date} 10:{30 + i * 10:02d}",
            duration=f"{2 + i // 3}h{i * 10}m",
            stops=0 if i % 3 != 0 else 1,
            stopoverCities=[] if i % 3 != 0 else ["XIY"],
            airline="中国国航" if i % 2 == 0 else "东方航空",
            airlineCode="CA" if i % 2 == 0 else "MU",
            price=1200 + i * 200,
            seatsRemaining=10 + i,
            cabin="economy"
        )
        mock_list.append(flight)
    return mock_list