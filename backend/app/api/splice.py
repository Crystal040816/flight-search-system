# backend/app/api/splice.py
from flask import Blueprint, request
from app.models.response import UnifiedResponse
from app.services.splice_service import splice_service

splice_bp = Blueprint('splice', __name__, url_prefix='/api')


@splice_bp.route('/splice', methods=['POST'])
def splice():
    """
    智能拼接接口 (已对接算法 route_graph 物理图配置)
    ---
    tags:
      - 拼接
    summary: 多段航班组合拼接
    description: 自动加载算法 route_graph，在内存中执行拓扑一中转算法，组合出最合理的拼装中转路线
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
              description: 出发地机场 IATA 三字码 (真实图谱起点)
              example: "ATL"
            destination:
              type: string
              description: 目的地机场 IATA 三字码 (真实图谱终点)
              example: "SFO"
            date:
              type: string
              format: date
              description: 出发日期 (2022-04-20 至 2022-06-21)
              example: "2022-06-08"
            maxStops:
              type: integer
              default: 1
              example: 1
    responses:
      200:
        description: 成功返回拼接组合好的路线列表
    """
    try:
        data = request.get_json()
        if not data:
            return UnifiedResponse.bad_request("请求体不能为空")

        required = ['departure', 'destination', 'date']
        for field in required:
            if field not in data:
                return UnifiedResponse.bad_request(f"缺少必填参数: {field}")

        departure = data.get('departure')
        destination = data.get('destination')
        date = data.get('date')
        max_stops = data.get('maxStops', 1)

        # 调用服务层进行最优中转航线拼接
        spliced_routes = splice_service.get_spliced_routes(
            departure, destination, date, max_stops
        )

        return UnifiedResponse.success({
            "routes": spliced_routes,
            "total": len(spliced_routes)
        })

    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")