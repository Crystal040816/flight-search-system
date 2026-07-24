# Flight System - Apache Zeppelin Code

## Notebook Note: 2MZABZFK3

### Paragraph 1: Data Reload & View Initialization (%pyspark)

```python
%pyspark
# 1. 配置 MySQL 参数
mysql_host = "127.0.0.1"
jdbc_url = f"jdbc:mysql://{mysql_host}:3306/flight_ads?useSSL=false&characterEncoding=UTF-8"
jdbc_user = "flight_ads_reader"
jdbc_password = "123456"

# 需要重新加载的 ADS 表列表
tables = ["ads_route_cabin_lowest_price", "ads_route_offer_rank", "ads_airline_offer_share"]

# 2. 清理旧视图与内存缓存（安全修复版）
print("🧹 正在清理旧的临时视图与缓存...")
for table in tables:
    # 只有当表/视图确实存在时，才去检查缓存和删除
    if spark.catalog.tableExists(table):
        if spark.catalog.isCached(table):
            spark.catalog.uncacheTable(table)
        spark.catalog.dropTempView(table)
        print(f"  └─ 成功清理旧视图: {table}")

# 清理 Spark SQL 的 Unused 内存缓存
spark.catalog.clearCache()
print("✅ 旧视图清理完毕！\n")

# 3. 重新读取 MySQL 并注册新视图
def reload_table(table_name):
    df = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", table_name) \
        .option("user", jdbc_user) \
        .option("password", jdbc_password) \
        .load()
    
    # 注册为全新临时视图
    df.createOrReplaceTempView(table_name)
    print(f"🔄 【{table_name}】重新加载成功！最新数据总行数: {df.count()}")
    return df

# 执行重新加载
df_lowest_price = reload_table("ads_route_cabin_lowest_price")
df_offer_rank   = reload_table("ads_route_offer_rank")
df_offer_share  = reload_table("ads_airline_offer_share")

print("\n🎉 所有临时视图已全部重置并重新生成！可以去重新运行后面的 %spark.sql 了。")
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