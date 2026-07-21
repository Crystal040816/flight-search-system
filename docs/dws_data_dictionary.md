# DWS 数据字典与使用说明

## 1. 层级定位

DWS 将 DWD 报价快照按搜索日期、市场航线、第一航段航司和市场机场汇总。数据位于 Hive `flight_db`，格式为 Parquet + Snappy。

所有统计均基于“搜索报价快照”：

- `quote_count` 不是订单量、客流量或真实执行航班量；
- `offer_share_pct` 是报价供给占比，不是销售市场份额；
- 航司归属使用报价的第一航段航司。

## 2. 表清单

| 表名 | 粒度 | 分区/逻辑键 | 当前行数 |
| --- | --- | --- | ---: |
| `dws_route_daily_stats` | 搜索日 + 市场航线 | `search_date + route_id` | 1,246 |
| `dws_airline_stats` | 搜索日 + 第一航段航司 | `search_date + airline_code` | 71 |
| `dws_airport_stats` | 搜索日 + 市场机场 | `search_date + market_airport_code` | 96 |
| `dws_route_profile` | 市场航线 | `route_id` | 234 |

前三张表按 `search_date` 分区；`dws_route_profile` 是跨当前样本日期的航线画像，不分区。

## 3. `dws_route_daily_stats`

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `route_id` | STRING | 市场航线标识 |
| `market_origin` | STRING | 市场起点机场代码 |
| `market_destination` | STRING | 市场终点机场代码 |
| `quote_count` | BIGINT | 当日该市场航线的报价快照数 |
| `distinct_leg_count` | BIGINT | 当日不同 `leg_id` 数量 |
| `avg_price` | DECIMAL(12,2) | 平均含税总价 |
| `min_price` | DECIMAL(12,2) | 最低含税总价 |
| `max_price` | DECIMAL(12,2) | 最高含税总价 |
| `avg_seats` | DECIMAL(12,2) | 平均剩余座位数 |
| `avg_duration_minutes` | DECIMAL(12,2) | 平均全程分钟数 |
| `nonstop_quote_count` | BIGINT | 直飞报价数 |
| `nonstop_quote_rate` | DECIMAL(9,6) | 直飞报价数 / 报价总数，范围 0 至 1 |
| `etl_time` | TIMESTAMP | ETL 处理时间 |
| `search_date` | DATE | 搜索日期，Hive 分区列 |

## 4. `dws_airline_stats`

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `airline_code` | STRING | 第一航段航司代码 |
| `airline_name` | STRING | 第一航段航司名称 |
| `quote_count` | BIGINT | 当日归属于该航司的报价数 |
| `distinct_leg_count` | BIGINT | 当日不同 `leg_id` 数量 |
| `avg_price` | DECIMAL(12,2) | 平均含税总价 |
| `min_price` | DECIMAL(12,2) | 最低含税总价 |
| `max_price` | DECIMAL(12,2) | 最高含税总价 |
| `offer_share_pct` | DECIMAL(9,6) | 当日报价供给百分比，所有航司合计约 100 |
| `etl_time` | TIMESTAMP | ETL 处理时间 |
| `search_date` | DATE | 搜索日期，Hive 分区列 |

## 5. `dws_airport_stats`

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `market_airport_code` | STRING | 用户搜索条件中的市场机场代码 |
| `origin_quote_count` | BIGINT | 作为市场起点的报价数 |
| `destination_quote_count` | BIGINT | 作为市场终点的报价数 |
| `avg_origin_price` | DECIMAL(12,2) | 作为市场起点时的平均含税总价 |
| `avg_destination_price` | DECIMAL(12,2) | 作为市场终点时的平均含税总价 |
| `etl_time` | TIMESTAMP | ETL 处理时间 |
| `search_date` | DATE | 搜索日期，Hive 分区列 |

## 6. `dws_route_profile`

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `route_id` | STRING | 市场航线标识 |
| `market_origin` | STRING | 市场起点机场代码 |
| `market_destination` | STRING | 市场终点机场代码 |
| `avg_distance_miles` | DECIMAL(12,2) | 当前样本中的平均全程距离 |
| `avg_duration_minutes` | DECIMAL(12,2) | 当前样本中的平均全程分钟数 |
| `first_seen_date` | DATE | 当前样本首次搜索日期 |
| `last_seen_date` | DATE | 当前样本最后搜索日期 |
| `etl_time` | TIMESTAMP | ETL 处理时间 |

## 7. 推荐用途与查询

算法可使用 DWS 构造路线热度、价格水平、直飞率和航司报价占比等聚合特征。展示层若只需要最终指标，应优先读取 MySQL ADS，而不是直接扫描 DWS。

```sql
SELECT
    search_date,
    route_id,
    quote_count,
    avg_price,
    nonstop_quote_rate
FROM flight_db.dws_route_daily_stats
WHERE search_date = DATE '2022-04-19'
ORDER BY quote_count DESC
LIMIT 20;
```

当前 6 个搜索日期不连续且数据量不均衡，`previous day` 或趋势分析指的是样本中相邻的可用搜索日期，不保证是自然日连续序列。
