# backend/app/api/search.py
from flask import Blueprint, request
from app.models.response import UnifiedResponse
from app.services.search_service import search_service as flight_search_service

search_bp = Blueprint('search', __name__, url_prefix='/api')


# ----------------------------------------------------------------
# 接口 1: 获取出发地城市列表 (直连物理 origin_city)
# ----------------------------------------------------------------
@search_bp.route('/search/cities/origins', methods=['GET'])
def get_origin_cities():
    """
    获取可用出发地城市列表接口
    ---
    tags:
      - 搜索
    summary: 获取所有出发城市 (直连数仓)
    description: 自动去重检索数仓物理表 ads_route_lowest_price 的 origin_city 字段。
    responses:
      200:
        description: 成功返回城市列表
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            data:
              type: array
              items:
                type: string
                example: "纽约"
    """
    try:
        cities = flight_search_service.get_active_origin_cities()
        return UnifiedResponse.success(cities)
    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")


# ----------------------------------------------------------------
# 接口 2: 获取目的地城市列表 (直连物理 destination_city)
# ----------------------------------------------------------------
@search_bp.route('/search/cities/destinations', methods=['GET'])
def get_destination_cities():
    """
    获取可用目的地城市列表接口
    ---
    tags:
      - 搜索
    summary: 获取所有目的地城市 (直连数仓)
    description: 检索并去重读取数仓物理表 ads_route_lowest_price 的 destination_city 字段。
    responses:
      200:
        description: 成功返回城市列表
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            data:
              type: array
              items:
                type: string
                example: "旧金山"
    """
    try:
        cities = flight_search_service.get_active_destination_cities()
        return UnifiedResponse.success(cities)
    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")


# ----------------------------------------------------------------
# 接口 3: 获取可用的起飞出行日期列表 (出发时间)
# ----------------------------------------------------------------
@search_bp.route('/search/dates', methods=['GET'])
def get_flight_dates():
    """
    获取系统可售出发起飞日期接口
    ---
    tags:
      - 搜索
    summary: 获取所有可用起飞出发日期 (直连数仓)
    description: 检索数仓中所有已存入报价的真实 flight_date 出发日期列表。
    responses:
      200:
        description: 成功返回日期数组
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            data:
              type: array
              items:
                type: string
                example: "2022-06-08"
    """
    try:
        dates = flight_search_service.get_active_flight_dates()
        return UnifiedResponse.success(dates)
    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")


# ----------------------------------------------------------------
# 接口 4: 获取可用的舱型列表 (直连物理 cabin_type 列)
# ----------------------------------------------------------------
@search_bp.route('/search/cabins', methods=['GET'])
def get_cabin_list():
    """
    获取可用舱型列表接口
    ---
    tags:
      - 搜索
    summary: 获取所有系统支持的舱型 (直连数仓 cabin_type 列)
    responses:
      200:
        description: 成功返回舱等列表
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            data:
              type: array
              items:
                type: string
                example: "economy"
    """
    try:
        cabins = flight_search_service.get_active_cabins()
        return UnifiedResponse.success(cabins)
    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")


# ----------------------------------------------------------------
# 接口 5: 获取出发机场 (支持按【出发城市 origin_city】联动筛选)
# ----------------------------------------------------------------
@search_bp.route('/search/airports/origins', methods=['GET'])
def get_origins_list():
    """
    获取可用出发地机场列表 (支持根据出发城市筛选)
    ---
    tags:
      - 搜索
    summary: 获取所有可用的出发机场
    description: 支持传入出发城市名称参数，在 SQL 级别直接过滤出发机场代码，例如 `?city=纽约`
    parameters:
      - name: city
        in: query
        required: false
        type: string
        description: 出发城市名称 (中文)
        example: "纽约"
    responses:
      200:
        description: 成功返回出发机场列表
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            data:
              type: array
              items:
                type: string
                example: "LGA"
    """
    try:
        city_filter = request.args.get('city')
        origins = flight_search_service.get_active_origins(city_filter)
        return UnifiedResponse.success(origins)
    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")


# ----------------------------------------------------------------
# 接口 6: 获取目的地机场 (支持根据目的地城市筛选)
# ----------------------------------------------------------------
@search_bp.route('/search/airports/destinations', methods=['GET'])
def get_destinations_list():
    """
    获取可用目的地机场列表 (支持目的地城市筛选)
    ---
    tags:
      - 搜索
    summary: 获取所有可用的目的地机场
    description: 支持传入目的地城市名称参数，在 SQL 级别直接过滤目的地机场代码，例如 `?city=纽约`
    parameters:
      - name: city
        in: query
        required: false
        type: string
        description: 目的地城市中文名称
        example: "纽约"
    responses:
      200:
        description: 成功返回目的地机场列表
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            data:
              type: array
              items:
                type: string
                example: "SFO"
    """
    try:
        city_filter = request.args.get('city')
        destinations = flight_search_service.get_active_destinations(city_filter)
        return UnifiedResponse.success(destinations)
    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")


# ----------------------------------------------------------------
# 接口 7: 获取可用航空公司列表 (航司)
# ----------------------------------------------------------------
@search_bp.route('/airlines', methods=['GET'])
def get_airlines_list():
    """
    获取可用航空公司列表
    ---
    tags:
      - 搜索
    summary: 获取合作的所有航空公司代码与名称 (直连数仓)
    responses:
      200:
        description: 成功返回对照列表
    """
    try:
        airlines = flight_search_service.get_active_airlines()
        return UnifiedResponse.success(airlines)
    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")


# ----------------------------------------------------------------
# 接口 8: 航班搜索核心多表联查 (根据出发/目的机场 + 起飞时间查询)
# ----------------------------------------------------------------
@search_bp.route('/search', methods=['POST'])
def search_flights():
    """
       高级航班指标联合搜索接口 (根据起飞、降落机场、出行日期进行精准检索)
       ---
       tags:
         - 搜索
       summary: 机票指标纯数仓驱动查询 (精准物理匹配版)
       description: "支持按出发机场、目的地机场、出行日期进行高精度的三表 (LEFT JOIN) 联合查询。返回 11 个核心业务指标。"
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
                 description: "出发地机场 IATA 三字码 (必填)"
                 example: "LGA"
               destination:
                 type: string
                 description: "目的地机场 IATA 三字码 (必填)"
                 example: "SFO"
               flightDate:
                 type: string
                 format: date
                 description: "起飞日期 (2022-04-20 至 2022-06-21) (必填)"
                 example: "2022-06-08"
               searchDate:
                 type: string
                 format: date
                 description: "搜索快照分区日 (2022-04-18 至 2022-04-27)"
                 default: "2022-04-19"
                 example: "2022-04-19"
               cabinCode:
                 type: string
                 description: "舱型筛选 (对应数仓 cabin_type 列)"
                 default: "economy"
                 example: "economy"
               page:
                 type: integer
                 default: 1
                 example: 1
               size:
                 type: integer
                 default: 10
                 example: 10
               sortBy:
                 type: string
                 enum: [price]
                 default: price
                 example: "price"
               filters:
                 type: object
                 properties:
                   airlines:
                     type: array
                     items:
                       type: string
                     example: ["UA", "DL"]
       responses:
         200:
           description: "成功返回多表联查宽表业务指标"
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
                   flights:
                     type: array
                     items:
                       type: object
                       properties:
                         legId:
                           type: string
                           example: "7a3ff1abd3aef9a..."
                         departureTime:
                           type: string
                           example: "2022-06-08 09:00"
                         duration:
                           type: string
                           example: "2h30m"
                         lowestPrice:
                           type: number
                           description: "出发日该航线最低含税报价 (USD)"
                           example: 166.61
                         avgPrice:
                           type: number
                           description: "出发日该航线平均含税报价 (USD)"
                           example: 240.50
                         routeRank:
                           type: integer
                           description: "当日该航线在数仓中的报价供给排名"
                           example: 12
                         previousDayAvgPrice:
                           type: number
                           description: "样本中前一日均价"
                           example: 235.00
                         priceChangePct:
                           type: number
                           description: "相对前一日的变价百分比"
                           example: 0.0234
                         routeQuoteCount:
                           type: integer
                           description: "该航线当日的搜索快照报价总数"
                           example: 320
                         distinctLegCount:
                           type: integer
                           description: "该航线当日的不同行程方案数"
                           example: 45
                         offerSharePct:
                           type: number
                           description: "执飞航司在当日的报价供给百分比 (占100的比例)"
                           example: 12.3456
                         airlineAvgPrice:
                           type: number
                           description: "该航司在当日的平均含税报价 (USD)"
                           example: 180.20
                         airline:
                           type: string
                           description: "执飞航空公司名称 (已补齐文档)"
                           example: "American Airlines"
                         airlineCode:
                           type: string
                           description: "执飞航空公司代码 (已补齐文档)"
                           example: "AA"
                         departure:
                           type: string
                           example: "LGA"
                         destination:
                           type: string
                           example: "SFO"
                         departureCity:
                           type: string
                           example: "纽约"
                         destinationCity:
                           type: string
                           example: "旧金山"
                         destinationCountryCode:
                           type: string
                           example: "US"
                         destinationCountryName:
                           type: string
                           example: "United States"
                         cabin:
                           type: string
                           example: "economy"
       """
    try:
        data = request.get_json()
        if not data:
            return UnifiedResponse.bad_request("请求体不能为空")

        required = ['departure', 'destination', 'flightDate']
        for field in required:
            if field not in data:
                return UnifiedResponse.bad_request(f"缺少必填参数: {field}")

        # 调用精准物理匹配的服务逻辑
        result = flight_search_service.search_flights(
            departure=data.get('departure'),
            destination=data.get('destination'),
            departure_city=data.get('departureCity'),
            destination_city=data.get('destinationCity'),
            flight_date=data.get('flightDate'),
            search_date=data.get('searchDate'),  # 去掉默认 '2022-04-19'，交给服务层动态匹配
            cabin_code=data.get('cabinCode'),  # 关键修改：去掉默认 'economy'，改用 None，不强制过滤
            page=data.get('page', 1),
            size=data.get('size', 20),
            sort_by=data.get('sortBy', 'price'),
            filters=data.get('filters', {})
        )

        return UnifiedResponse.success(result)

    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")