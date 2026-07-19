# backend/app/api/splice.py
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from app.models.request import SpliceRequest
from app.models.response import UnifiedResponse
from app.models.flight import FlightSegment, SplicedRoute
from app.services.splice_service import splice_service

splice_bp = Blueprint('splice', __name__, url_prefix='/api')


@splice_bp.route('/splice', methods=['POST'])
def splice():
    """
    智能拼接接口
    ---
    tags:
      - 拼接
    summary: 多段航班组合拼接
    description: 通过中转组合出高性价比路线
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - departure
            - destination
            - date
          properties:
            departure:
              type: string
              example: PEK
            destination:
              type: string
              example: CDG
            date:
              type: string
              format: date
              example: "2026-08-01"
            maxStops:
              type: integer
              default: 2
              example: 2
    responses:
      200:
        description: 成功
    """
    try:
        data = request.get_json()
        if not data:
            return UnifiedResponse.bad_request("请求体不能为空")

        required = ['departure', 'destination', 'date']
        for field in required:
            if field not in data:
                return UnifiedResponse.bad_request(f"缺少必填参数: {field}")

        # TODO: 组员B提供拼接算法
        departure = data.get('departure')
        destination = data.get('destination')
        date = data.get('date')
        max_stops = data.get('maxStops', 2)

        # 调用服务层进行最优中转航线拼接
        spliced_routes = splice_service.get_spliced_routes(
            departure, destination, date, max_stops
        )

        return UnifiedResponse.success({
            "routes": spliced_routes,
            "total": len(spliced_routes)
        })
        # # 当前返回 Mock 数据
        # mock_routes = [
        #     SplicedRoute(
        #         totalPrice=9000,
        #         totalDuration="15h",
        #         stops=1,
        #         segments=[
        #             FlightSegment(
        #                 from_airport=data.get('departure', 'PEK'),
        #                 to_airport="DOH",
        #                 airline="卡塔尔航空",
        #                 airlineCode="QR",
        #                 departureTime=f"{data.get('date')} 01:00",
        #                 arrivalTime=f"{data.get('date')} 05:00",
        #                 price=3000,
        #                 duration="4h"
        #             ),
        #             FlightSegment(
        #                 from_airport="DOH",
        #                 to_airport=data.get('destination', 'CDG'),
        #                 airline="卡塔尔航空",
        #                 airlineCode="QR",
        #                 departureTime=f"{data.get('date')} 08:00",
        #                 arrivalTime=f"{data.get('date')} 13:00",
        #                 price=6000,
        #                 duration="5h"
        #             )
        #         ]
        #     )
        # ]
        #
        # return UnifiedResponse.success({
        #     "routes": [r.to_dict() for r in mock_routes],
        #     "total": len(mock_routes)
        # })

    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")