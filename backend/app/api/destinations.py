# backend/app/api/destinations.py
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from app.models.request import DestinationsRequest
from app.models.response import UnifiedResponse
from app.models.flight import DestinationInfo

destinations_bp = Blueprint('destinations', __name__, url_prefix='/api')


@destinations_bp.route('/destinations', methods=['POST'])
def get_destinations():
    """
    飞去哪接口
    ---
    tags:
      - 目的地
    summary: 查询各目的地最低价
    description: 输入出发地和日期，返回所有可达目的地的最低价格
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - departure
            - date
          properties:
            departure:
              type: string
              example: PEK
            date:
              type: string
              format: date
              example: "2026-08-01"
    responses:
      200:
        description: 成功
    """
    try:
        data = request.get_json()
        if not data:
            return UnifiedResponse.bad_request("请求体不能为空")

        required = ['departure', 'date']
        for field in required:
            if field not in data:
                return UnifiedResponse.bad_request(f"缺少必填参数: {field}")

        # TODO: 组员A提供数据，组员C实现真实查询
        # 当前返回 Mock 数据
        mock_destinations = [
            DestinationInfo(
                destination="PVG",
                city="上海",
                country="中国",
                lowestPrice=800
            ),
            DestinationInfo(
                destination="HKG",
                city="香港",
                country="中国",
                lowestPrice=1200
            ),
            DestinationInfo(
                destination="SIN",
                city="新加坡",
                country="新加坡",
                lowestPrice=2500
            ),
            DestinationInfo(
                destination="BKK",
                city="曼谷",
                country="泰国",
                lowestPrice=1800
            )
        ]

        return UnifiedResponse.success({
            "destinations": [d.to_dict() for d in mock_destinations],
            "total": len(mock_destinations)
        })

    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")