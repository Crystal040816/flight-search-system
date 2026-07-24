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
    description: 输入出发城市名称和飞行起飞日期，自适应动态检索最大快照分区，计算并拼装出完整的起降迁徙指标。
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - departureCity
            - flightDate
          properties:
            departureCity:
              type: string
              description: "出发城市中文名称 (直接对应数仓 origin_city 字段)"
              example: "纽约"
            flightDate:
              type: string
              format: date
              description: "出行起飞日期 (2022-04-20 至 2022-06-21)"
              example: "2022-06-08"
            searchDate:
              type: string
              format: date
              description: "搜索快照分区日期 (选填，不传则自动匹配该起降路线有数据的最新分区)"
              example: "2022-04-19"
    responses:
      200:
        description: 成功返回目的地最低报价排行与起降指标
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
        flight_date = data.get('date')
        # 允许不传 searchDate，交由 Service 层去 SQL 级执行动态的最大日期自适应
        search_date = data.get('searchDate')

        # 调用服务层
        results = destinations_service.get_lowest_price_destinations(departure_city, flight_date, search_date)

        return UnifiedResponse.success({
            "destinations": results,
            "total": len(results)
        })
    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")