# Flight System - Apache Zeppelin Code

## Notebook Note: 2MZABZFK3

### Paragraph 1: Data Reload & View Initialization (%sql)

```sql
%sql
-- 1. 创建映射到 MySQL 的外表（只需要运行一次，即使重启 Zeppelin 也永久有效）

CREATE TABLE IF NOT EXISTS ads_route_cabin_lowest_price
USING org.apache.spark.sql.jdbc
OPTIONS (
  url 'jdbc:mysql://127.0.0.1:3306/flight_ads?useSSL=false&characterEncoding=UTF-8',
  dbtable 'ads_route_cabin_lowest_price',
  user 'flight_ads_reader',
  password '123456'
);

CREATE TABLE IF NOT EXISTS ads_route_offer_rank
USING org.apache.spark.sql.jdbc
OPTIONS (
  url 'jdbc:mysql://127.0.0.1:3306/flight_ads?useSSL=false&characterEncoding=UTF-8',
  dbtable 'ads_route_offer_rank',
  user 'flight_ads_reader',
  password '123456'
);

CREATE TABLE IF NOT EXISTS ads_airline_offer_share
USING org.apache.spark.sql.jdbc
OPTIONS (
  url 'jdbc:mysql://127.0.0.1:3306/flight_ads?useSSL=false&characterEncoding=UTF-8',
  dbtable 'ads_airline_offer_share',
  user 'flight_ads_reader',
  password '123456'
);
```

---

### Paragraph 2: 热门航线 TOP 15 (%sql)

```sql
%sql
-- 1. 热门航线 TOP 15
SELECT 
    CONCAT(market_origin, ' ➔ ', market_destination) AS `航线`,
    quote_count AS `热度(报价数)`,
    avg_price AS `航线均价(USD)`
FROM ads_route_offer_rank
WHERE search_date = '${搜索日期=2022-04-18,2022-04-18|2022-04-19|2022-04-22|2022-04-23|2022-04-26|2022-04-27}'
ORDER BY quote_count DESC
LIMIT 15;
```

---

### Paragraph 3: 价格跳水榜 (%sql)

```sql
%sql
-- 2.1 价格跳水榜
SELECT 
    CONCAT(market_origin, ' ➔ ', market_destination) AS `航线`,
    avg_price AS `今日均价`,
    previous_day_avg_price AS `昨日均价`,
    ROUND(price_change_pct, 2) AS `跌幅(%)`,
    '🔥 值得抄底' AS `系统建议`
FROM ads_route_offer_rank
WHERE search_date = '${搜索日期=2022-04-18,2022-04-18|2022-04-19|2022-04-22|2022-04-23|2022-04-26|2022-04-27}'
  AND price_change_pct IS NOT NULL
ORDER BY price_change_pct ASC
LIMIT 20;
```

---

### Paragraph 4: 价格暴涨预警榜 (%sql)

```sql
%sql
-- 2.2 价格暴涨预警榜
SELECT 
    CONCAT(market_origin, ' ➔ ', market_destination) AS `航线`,
    avg_price AS `今日均价`,
    previous_day_avg_price AS `昨日均价`,
    ROUND(price_change_pct, 2) AS `涨幅(%)`,
    '⚠️ 建议及早订票' AS `系统建议`
FROM ads_route_offer_rank
WHERE search_date = '${搜索日期=2022-04-18,2022-04-18|2022-04-19|2022-04-22|2022-04-23|2022-04-26|2022-04-27}'
  AND price_change_pct IS NOT NULL
ORDER BY price_change_pct DESC
LIMIT 20;
```

---

### Paragraph 5: 临期余票预警与低价抢购 (%sql)

```sql
%sql
-- 3. 临期（7天内出发）且余票少的低价航班
SELECT 
    CONCAT(origin_city, ' ➔ ', destination_city) AS `航线`,
    flight_date AS `起飞日期`,
    DATEDIFF(flight_date, search_date) AS `距起飞天数`,
    airline_name AS `航空公司`,
    cabin_type AS `舱位类型`,
    seats_remaining AS `剩余座位数`,
    lowest_price AS `抢购价(USD)`
FROM ads_route_cabin_lowest_price
WHERE search_date = '${搜索日期=2022-04-18,2022-04-18|2022-04-19|2022-04-22|2022-04-23|2022-04-26|2022-04-27}'
  AND origin_city = '${出发城市=New York,Atlanta|Boston|Charlotte|Chicago|Dallas-Fort Worth|Denver|Detroit|Dulles|Los Angeles|Miami|New York|Newark|Oakland|Philadelphia|San Francisco}'
  AND seats_remaining > 0
  AND seats_remaining <= CAST('${最大剩余座位=5}' AS INT)
  AND DATEDIFF(flight_date, search_date) BETWEEN 0 AND 7
ORDER BY 
  CASE WHEN '${排序方式=seats_asc,seats_asc|days_asc|price_asc}' = 'seats_asc' THEN seats_remaining END ASC,
  CASE WHEN '${排序方式=seats_asc,seats_asc|days_asc|price_asc}' = 'days_asc' THEN DATEDIFF(flight_date, search_date) END ASC,
  CASE WHEN '${排序方式=seats_asc,seats_asc|days_asc|price_asc}' = 'price_asc' THEN lowest_price END ASC,
  lowest_price ASC -- 次要排序兜底
```