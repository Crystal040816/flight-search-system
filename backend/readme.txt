机票智能决策系统 API 技术规约 (API Document)
一、 全局规范
1. 服务网关 Base URL: http://192.168.100.27:5000/api
2. 数据承载协议: application/json，字符集为 UTF-8。
3. 物理币种规约: 全量价格及金额指标采用 USD（美元）。

二、 统一响应外壳 (UnifiedResponse JSON)
无论请求成功还是发生异常，网关统一通过以下结构返回，便于前端拦截器统一处理：
{
  "code": 200,          // 业务状态码：200 成功，400 参数校验错误，500 服务器计算崩溃
  "message": "success", // 状态说明描述
  "data": {}            // 实际返回的数据体 (失败或空时为 null/空数组)
}


三、 核心 API 路由明细

-----------------------------------------------------------------------------
[接口 1] 获取可用出发城市列表
-----------------------------------------------------------------------------
* 请求方法：GET
* 请求路径：/search/cities/origins
* 接口说明：去重检索数仓物理表 ads_route_cabin_lowest_price 中的 origin_city 出发城市字段。
* 成功响应体 (200 OK)：
{
  "code": 200,
  "data": [
    "Atlanta",
    "Boston",
    "Charlotte",
    "Chicago",
    "Dallas-Fort Worth",
    "Denver",
    "Detroit",
    "Dulles",
    "Los Angeles",
    "Miami",
    "New York",
    "Newark",
    "Oakland",
    "Philadelphia",
    "San Francisco"
  ],
  "message": "success"
}

-----------------------------------------------------------------------------
[接口 2] 获取可用目的地城市列表
-----------------------------------------------------------------------------
* 请求方法：GET
* 请求路径：/search/cities/destinations
* 接口说明：去重检索数仓物理表 ads_route_cabin_lowest_price 的 destination_city 目的地城市字段。
* 成功响应体 (200 OK)：
{
  "code": 200,
  "data": [
    "Atlanta",
    "Boston",
    "Charlotte",
    "Chicago",
    "Dallas-Fort Worth",
    "Denver",
    "Detroit",
    "Dulles",
    "Los Angeles",
    "Miami",
    "New York",
    "Newark",
    "Oakland",
    "Philadelphia",
    "San Francisco"
  ],
  "message": "success"
}


-----------------------------------------------------------------------------
[接口 3] 获取可用的起飞出行日期列表
-----------------------------------------------------------------------------
* 请求方法：GET
* 请求路径：/search/dates
* 接口说明：检索数仓中所有已存入报价的真实 flight_date 出发日期列表。
* 成功响应体 (200 OK)：
{
  "code": 200,
  "data": [
    "2022-04-20",
     ],
  "message": "success"
}

-----------------------------------------------------------------------------
[接口 4] 获取可售的舱型列表
-----------------------------------------------------------------------------
* 请求方法：GET
* 请求路径：/search/cabins
* 接口说明：检索并去重读取数仓物理表 cabin_type 列中真实存在的物理舱等。
* 成功响应体 (200 OK)：
{
  "code": 200,
  "message": "success",
  "data": [
    "business",
    "coach",
    "first",
    "mixed",
    "premium coach"
  ],
}


-----------------------------------------------------------------------------
[接口 5] 获取出发机场 - 支持城市二级联动
-----------------------------------------------------------------------------
* 请求方法：GET
* 请求路径：/search/airports/origins
* 接口说明：支持传入出发城市名称参数（URL 问号参数）执行 SQL 级过滤。
* 请求参数：city (string, 选填) - 出发城市名称 (如：New York)
* 成功响应体 (200 OK)：
{
  "code": 200,
  "data": [
    "ATL",
    "BOS",
    "CLT",
    "DEN",
    "DFW",
    "DTW",
    "EWR",
    "IAD",
    "JFK",
    "LAX",
    "LGA",
    "MIA",
    "OAK",
    "ORD",
    "PHL",
    "SFO"
  ],
  "message": "success"
}

-----------------------------------------------------------------------------
[接口 6] 获取目的地机场 - 支持城市二级联动
-----------------------------------------------------------------------------
* 请求方法：GET
* 请求路径：/search/airports/destinations
* 接口说明：支持传入目的地城市名称参数执行 SQL 级过滤。
* 请求参数：city (string, 选填) - 目的地城市名称 (如：San Francisco)
* 成功响应体 (200 OK)：
{
  "code": 200,
  "data": [
    "ATL",
    "BOS",
    "CLT",
    "DEN",
    "DFW",
    "DTW",
    "EWR",
    "IAD",
    "JFK",
    "LAX",
    "LGA",
    "MIA",
    "OAK",
    "ORD",
    "PHL",
    "SFO"
  ],
  "message": "success"
}

-----------------------------------------------------------------------------
[接口 7] 获取可用航空公司列表
-----------------------------------------------------------------------------
* 请求方法：GET
* 请求路径：/airlines
* 接口说明：获取当前数仓中所有合作的航空公司两字码及其实时中文名称。
* 成功响应体 (200 OK)：
{
  "code": 200,
  "data": [
    {
      "code": "4B",
      "name": "Boutique Air"
    },
   {
      "code": "9K",
      "name": "Cape Air"
    },
    {
      "code": "9X",
      "name": "Southern Airways Express"
    },
    ],
  "message": "success"
}

-----------------------------------------------------------------------------
[接口 8] 航班多表联查核心检索
-----------------------------------------------------------------------------
* 请求方法：POST
* 请求路径：/search
* 接口说明：根据起降机场、起飞出行日期，在 MySQL 端执行三表（最低价表、航线排行表、航司占比表）LEFT JOIN 联合查询，输出 11 个大屏核心业务指标。
* 请求体参数 (Request Body JSON)：
{
  "cabinCode": "coach",
  "departure": "ATL",
  "destination": "BOS",
  "filters": {
    "airlines": [
    ]
  },
  "flightDate": "2022-04-24",
  "page": 1,
  "searchDate": "2022-04-19",
  "size": 10,
  "sortBy": "price"
}
* 成功响应体 (200 OK)：
{
  "code": 200,
  "data": {
    "flights": [
      {
        "aircraftModel": "Airbus A321||Embraer 170||Boeing 737-700",
        "airline": "Delta",
        "airlineAvgPrice": 380.72,
        "airlineCode": "DL",
        "arrivalTime": "2022-04-25, 09:24:00",
        "avgPrice": 482.71,
        "cabin": "coach",
        "cabinSummary": "coach||coach||coach",
        "departure": "ATL",
        "departureCity": "Atlanta",
        "departureCountryCode": "US",
        "departureCountryName": "United States",
        "departureTime": "2022-04-24, 23:20:00",
        "destination": "BOS",
        "destinationCity": "Boston",
        "destinationCountryCode": "US",
        "destinationCountryName": "United States",
        "distinctLegCount": 2198,
        "duration": "10时4分",
        "isMixedCabin": false,
        "legId": "bdfb47476040fa7c79b590f4659b1966b6ceda621e92f9c2d3e49705e27f2460",
        "lowestPrice": 482.71,
        "offerSharePct": 25.236925,
        "previousDayAvgPrice": 0,
        "price": 482.71,
        "priceChangePct": 0,
        "routeQuoteCount": 2198,
        "routeRank": 32,
        "seatsRemaining": 1,
        "stops": 0
      },
	#剩余航班省略，在此不做展示
        ],
    "total": 23
  },
  "message": "success"
}

-----------------------------------------------------------------------------
[接口 9] 机票价格趋势推演预测
-----------------------------------------------------------------------------
* 请求方法：POST
* 请求路径：/predict
* 接口说明：自动组装 18 维特征矩阵，调起物理 XGBoost 预测模型 price_predict_model.pkl 执行从搜索快照日到起飞日期之间的每日票价推演。
* 请求体参数 (Request Body JSON)：
{
  "departure": "LGA",
  "destination": "SFO",
  "flightDate": "2022-06-08",
  "days": 7                        // 需要往后推演和预测的价格趋势天数 (选填，默认7)
}
* 成功响应体 (200 OK)：
{
  "code": 200,
  "data": {
    "bestBuy": {
      "date": "2022-04-23",
      "daysToDeparture": 46,
      "price": 297.92
    },
    "departure": "ATLANTA",
    "destination": "NEW YORK",
    "startDate": "2022-06-08",
    "statistics": {
      "avgPrice": 298.27,
      "maxPrice": 298.48,
      "minPrice": 297.92,
      "totalDays": 7
    },
    "suggestion": "价格相对稳定，建议保持关注。最佳购买日期：2022-04-23，价格：$297.92",
    "totalDays": 7,
    "trend": [
      {
        "date": "2022-04-19",
        "daysToDeparture": 50,
        "predictedPrice": 298.48
      },
      {
        "date": "2022-04-20",
        "daysToDeparture": 49,
        "predictedPrice": 298.48
      },
      {
        "date": "2022-04-21",
        "daysToDeparture": 48,
        "predictedPrice": 298.48
      },
      {
        "date": "2022-04-22",
        "daysToDeparture": 47,
        "predictedPrice": 298.27
      },
      {
        "date": "2022-04-23",
        "daysToDeparture": 46,
        "predictedPrice": 297.92
      },
      {
        "date": "2022-04-24",
        "daysToDeparture": 45,
        "predictedPrice": 297.99
      },
      {
        "date": "2022-04-25",
        "daysToDeparture": 44,
        "predictedPrice": 298.27
      }
    ]
  },
  "message": "success"
}

-----------------------------------------------------------------------------
[接口 10] 多段航班智能中转拼接
-----------------------------------------------------------------------------
* 请求方法：POST
* 请求路径：/splice
* 接口说明：加载算法拼接邻接表（图数据）splice_model.pkl，在内存中执行一中转（One-Stop）路线拓扑搜索，并直连数仓动态捞取并累加当日各航段的真实最低票价。
* 请求体参数 (Request Body JSON)：
{
  "date": "2022-04-23",
  "departure": "ATL",
  "destination": "MIA",
  "maxStops": 1
}
* 成功响应体 (200 OK)：
{
  "code": 200,
  "data": {
    "routes": [
      {
        "legId": "spliced_ATL_BOS_MIA_2022-04-23",
        "segments": [
          {
            "aircraftModel": "Airbus A321||Embraer 175",
            "airline": "Delta",
            "airlineCode": "DL",
            "arrivalTime": "2022-04-23 08:30",
            "departureTime": "2022-04-23 06:00",
            "duration": "2h30m",
            "fromAirport": "ATL",
            "price": 637.2,
            "toAirport": "BOS"
          },
          {
            "aircraftModel": "Embraer 175||Boeing 737-800",
            "airline": "American Airlines",
            "airlineCode": "AA",
            "arrivalTime": "2022-04-23 14:00",
            "departureTime": "2022-04-23 11:30",
            "duration": "2h30m",
            "fromAirport": "BOS",
            "price": 156.6,
            "toAirport": "MIA"
          }
        ],
        "stops": 1,
        "totalDuration": "8h0m",
        "totalPrice": 793.8000000000001
      },
      ],
        "stops": 1,
        "totalDuration": "8h0m",
        "totalPrice": 793.8000000000001
      }
#余下省略，在此不做展示
    ],
    "total": 5
  },
  "message": "success"
}

-----------------------------------------------------------------------------
[接口 11] 飞去哪目的地低价地图排行
-----------------------------------------------------------------------------
* 请求方法：POST
* 请求路径：/destinations
* 接口说明：输入出发城市中文名和出行起飞日期，自适应动态在 MySQL 物理表中执行 MIN 聚合，算出所有可达目的地的最低票价排行，支撑前端迁徙图/气泡展示。
* 请求体参数 (Request Body JSON)：
{
  "departureCity": "Boston",         // 出发城市中文/英文名 (对应物理 origin_city) (必填)
  "date": "2022-04-23",              // 起飞出行日期 (必填)
  "searchDate": "2022-04-19",
}
* 成功响应体 (200 OK)：
{
  "code": 200,
  "data": {
    "destinations": [
      {
        "city": "Miami",
        "continent": "N/A",
        "country": "United States",
        "departure": "BOS",
        "departureCity": "Boston",
        "destination": "MIA",
        "lowestPrice": 61.97
      },
  #余下省略，在此不做展示
    ],
    "total": 15
  },
  "message": "success"

-----------------------------------------------------------------------------
[接口 12] 智能多因素推荐排行接口
-----------------------------------------------------------------------------
* 请求方法：POST
* 请求路径：/api/recommend
* 接口说明：多表联查抽取当日 50 条候选航班组成推荐池。自动反序列化加载模型 weights 权重配置 recommend_model.pkl。在 Python 内存级对价格、中转、机型、航司、座位数进行五维 Min-Max 归一化综合打分计算（totalScore），按得分降序返回 Top 10 个最推荐的行程卡片。
* 请求体参数 (Request Body JSON)：
{
  "departure": "ATL",                    // 出发地机场 (必填)
  "destination": "BOS",                  // 目的地机场 (必填)
  "flightDate": "2022-04-24",            // 出行起飞日期 (2022-04-20 至 2022-06-21) (必填)
  "preferences": {                       // 用户的个性化偏好选择过滤器 (选填)
    "preferLowPrice": true,              // 是否偏好低价
    "preferShortDuration": false,        // 是否偏好短飞行时间
    "preferDirect": true                 // 是否偏好直飞
  }
}
* 成功响应体 (200 OK)：
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 1,                          // 推荐列表中的航班数量
    "recommendations": [
      {
        "flight": {
          "legId": "7a3ff1abd3aef9a65ea92fb3d4ae498cec6f846736f8df88c206ef75ee5ca5ce",
          "departureTime": "2022-06-08, 15:51:00",
          "arrivalTime": "2022-06-08, 17:51:00",
          "duration": "2时5分",
          "lowestPrice": 166.61,         // 最低含税票价 (USD)
          "avgPrice": 240.50,            // 该航线当日平均价格 (USD)
          "routeRank": 12,               // 航线当日报价供给量排名
          "previousDayAvgPrice": 235.00, // 前一个可用搜索日的日均价 (USD)
          "priceChangePct": 0.0234,      // 相对前一日的变价百分比
          "routeQuoteCount": 320,        // 航线当日的搜索快照报价总数
          "distinctLegCount": 45,        // 航线当日的不同行程方案数
          "offerSharePct": 12.3456,      // 执飞航司在当日的报价供给占比 (%)
          "airlineAvgPrice": 180.20,     // 该航司在当日该航线的平均含税报价 (USD)
          "airline": "American Airlines",
          "airlineCode": "AA",
          "departure": "LGA",
          "departureCity": "New York",
          "departureCountryCode": "US",
          "departureCountryName": "United States",
          "destination": "SFO",
          "destinationCity": "San Francisco",
          "destinationCountryCode": "US",
          "destinationCountryName": "United States",
          "cabin": "economy",
          "cabinSummary": "coach",
          "isMixedCabin": false,
          "stops": 0,
          "aircraftModel": "Boeing 737",
          "seatsRemaining": 7,
          "totalScore": 0.8543           // 算法加载权重算出的归一化综合推荐评分
        }
        "rank": 1,                       // 推荐排名 (算法打分从高到低排列)
        "reason": "综合性价比打分高达 0.8543，全网第 1 推荐", // 算法生成的推荐理由
      }
    ]
  }
}
}=============================================================================