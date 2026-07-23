# backend/app/api/destinations.py
from flask import Blueprint, request
from app.models.response import UnifiedResponse
from app.services.destinations_service import destinations_service

destinations_bp = Blueprint('destinations', __name__, url_prefix='/api')


@destinations_bp.route('/destinations', methods=['POST'])
def get_destinations():
    """
        飞去哪地图展示接口 (直连 MySQL 物理聚合查询)
        ---
        tags:
          - 目的地
        summary: 查询各目的地最低报价排行 (目的地地图数据源)
        description: "输入出发城市名称和飞行日期，自动在数据库中进行多字段 MIN 聚合，计算并拼装出完整的起降迁徙指标。"
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              required:
                - departureCity
                - date
              properties:
                departureCity:
                  type: string
                  description: "出发城市中文名称 (直接对应数仓 origin_city 字段)"
                  example: "纽约"
                date:
                  type: string
                  format: date
                  description: "搜索快照分区日期 (如 2022-04-19)"
                  example: "2022-04-19"
        responses:
          200:
            description: "成功返回目的地最低报价排行与起降指标"
            schema:
              type: object
              properties:
                code:
                  type: integer
                  example: 200
                data:
                  type: object
                  properties:
                    total:
                      type: integer
                      example: 1
                    destinations:
                      type: array
                      items:
                        type: object
                        properties:
                          departureCity:
                            type: string
                            example: "纽约"
                          departure:
                            type: string
                            example: "LGA"
                          city:
                            type: string
                            example: "旧金山"
                          destination:
                            type: string
                            example: "SFO"
                          country:
                            type: string
                            example: "United States"
                          continent:
                            type: string
                            example: "N/A"
                          lowestPrice:
                            type: number
                            example: 240.00

    """
    try:
        data = request.get_json()
        if not data:
            return UnifiedResponse.bad_request("请求体不能为空")

        required = ['departureCity', 'date']
        for field in required:
            if field not in data:
                return UnifiedResponse.bad_request(f"缺少必填参数: {field}")

        departure_city = data.get('departureCity')
        date = data.get('date')

        # 调用真实数仓聚合接口
        results = destinations_service.get_lowest_price_destinations(departure_city, date)

        return UnifiedResponse.success({
            "destinations": results,
            "total": len(results)
        })
    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")