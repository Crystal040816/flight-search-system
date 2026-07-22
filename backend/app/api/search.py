# backend/app/api/search.py
from flask import Blueprint, request
from app.models.response import UnifiedResponse
# 1. 明确导入具体的服务实例，避免 IDE 识别错误
from app.services.search_service import search_service as flight_search_service

search_bp = Blueprint('search', __name__, url_prefix='/api')

# 请在 backend/app/api/search.py 中，注册 search_bp 下方加入：

@search_bp.route('/airports', methods=['GET'])
def get_airports_list():
    """
    获取可用机场/城市列表接口
    ---
    tags:
      - 搜索
    summary: 获取系统所有可用机场
    description: 自动提取数仓中所有已有的、可供检索的机场三字码与城市名称，支持前端下拉框和模糊联想。
    responses:
      200:
        description: 成功返回机场列表
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            data:
              type: array
              items:
                type: object
                properties:
                  code:
                    type: string
                    description: 机场 IATA 三字码
                    example: ORD
                  city:
                    type: string
                    description: 城市中文名
                    example: 芝加哥
                  airport:
                    type: string
                    description: 机场详细名称
                    example: 奥黑尔国际机场
    """
    try:
        # 调用服务层提取
        from app.services.search_service import search_service
        airports = search_service.get_active_airports()
        return UnifiedResponse.success(airports)
    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")

@search_bp.route('/airlines', methods=['GET'])
def get_airlines_list():
    """
    获取可用航空公司列表接口
    ---
    tags:
      - 搜索
    summary: 获取系统所有可用航空公司
    description: 自动提取数仓中所有已有的、可供筛选的航空公司两字码及其中文名称对照，供前端多选过滤。
    responses:
      200:
        description: 成功返回航司代码与名称对照列表
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            data:
              type: array
              items:
                type: object
                properties:
                  code:
                    type: string
                    description: 航司 IATA 两字码
                    example: UA
                  name:
                    type: string
                    description: 航司中文名称
                    example: 联合航空
    """
    try:
        from app.services.search_service import search_service
        airlines = search_service.get_active_airlines()
        return UnifiedResponse.success(airlines)
    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")


@search_bp.route('/search', methods=['POST'])
def search_flights():
    """
    航班搜索接口 (已对接数仓 ES 数据源)
    ---
    tags:
      - 搜索
    summary: 实时搜索航班
    description: 根据出发地、目的地、日期搜索航班，支持单程/往返/多程。已对齐数仓规范，使用 legId 作为行程方案的唯一标识。
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
        description: 成功返回符合要求的航班行程方案列表
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
                      legId:
                        type: string
                        description: 行程方案唯一识别码 (替代原 flightNumber)
                        example: leg_PEK_PVG_001
                      price:
                        type: number
                        description: 包含总税费的总价格
                        example: 1200.00
                      departureTime:
                        type: string
                        example: "2026-07-20 08:30"
                      arrivalTime:
                        type: string
                        example: "2026-07-20 11:00"
                      duration:
                        type: string
                        example: "2h30m"
                      stops:
                        type: integer
                        description: 中转次数 (0为直飞)
                        example: 0
                      airline:
                        type: string
                        example: "中国国航"
                      airlineCode:
                        type: string
                        example: "CA"
                      aircraftModel:
                        type: string
                        description: 飞机机型设备描述 (对应 DWD equipment_description)
                        example: "Boeing 737"
    """
    try:
        data = request.get_json()
        if not data:
            return UnifiedResponse.bad_request("请求体不能为空")

        required = ['departure', 'destination', 'flightDate']
        for field in required:
            if field not in data:
                return UnifiedResponse.bad_request(f"缺少必填参数: {field}")

        # 2. 调用更新后的服务层实例方法
        result = flight_search_service.search_flights(
            departure=data.get('departure'),
            destination=data.get('destination'),
            flight_date=data.get('flightDate'),
            page=data.get('page', 1),
            size=data.get('size', 20),
            sort_by=data.get('sortBy', 'price'),
            filters=data.get('filters', {})
        )

        return UnifiedResponse.success(result)

    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")