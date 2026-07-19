# backend/app/api/destinations.py
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from app.models.request import DestinationsRequest
from app.models.response import UnifiedResponse
from app.models.flight import DestinationInfo
from app.services.destinations_service import destinations_service

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
        departure = data.get('departure')
        date = data.get('date')

        # 调用数仓接口
        results = destinations_service.get_lowest_price_destinations(departure, date)

        return UnifiedResponse.success({
            "destinations": results,
            "total": len(results)
        })
    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")