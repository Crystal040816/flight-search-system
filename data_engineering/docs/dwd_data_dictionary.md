# DWD 数据字典与使用说明

## 1. 层级定位

DWD 保存完成类型转换、业务校验、航段展开和异常分流后的可信明细。表位于 Hive `flight_db`，使用 Parquet + Snappy；算法和进一步聚合优先通过 Hive Metastore 读取。

当前事实数据是教学样本：从 82,138,753 条 ODS 报价中按 `FIRST_N_ROWS` 取 1,000,000 条。该方式不是随机抽样或日期均衡抽样。

## 2. 表清单和当前规模

| 表名 | 粒度/用途 | 关联键或分区 | 当前行数 |
| --- | --- | --- | ---: |
| `dwd_flight_itinerary` | 一条有效报价快照一行 | `quote_snapshot_id`；按 `search_date` 分区 | 1,000,000 |
| `dwd_flight_segments` | 报价中的一个实际航段一行 | `quote_snapshot_id + segment_index`；按 `search_date` 分区 | 1,785,428 |
| `dwd_route_info` | 一条市场起终点航线一行 | `route_id` | 234 |
| `dwd_itinerary_reject` | 一条被拒绝的原始报价一行 | 按 `process_date` 分区 | 0 |
| `dim_country` | 一个国家/地区一行 | `country_id` / `country_code` | 248 |
| `dim_region` | 一个行政区域一行 | `region_id` / `region_code` | 3,935 |
| `dim_airport` | 一个机场一行 | `airport_id` / `ident` / `iata_code` | 79,587 |
| `dwd_airport_runway` | 一条跑道一行 | `runway_id`、`airport_id` | 45,890 |
| `dwd_airport_frequency` | 一条机场频率一行 | `frequency_id`、`airport_id` | 29,376 |
| `dwd_navaid` | 一个导航台一行 | `navaid_id` | 11,020 |

`dq_check_result` 是跨层质量结果表，详见 `data_engineering/hive/dq_check_result_guide.md`。

## 3. `dwd_flight_itinerary`

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `quote_snapshot_id` | STRING | ETL 根据稳定业务字段生成的报价快照唯一标识 |
| `leg_id` | STRING | 航程标识，不能单独作为报价唯一键 |
| `flight_date` | DATE | 出发日期 |
| `market_origin` | STRING | 搜索起点市场机场 IATA 代码 |
| `market_destination` | STRING | 搜索终点市场机场 IATA 代码 |
| `fare_basis_code` | STRING | 票价基础代码 |
| `first_airline_code` | STRING | 第一航段航司代码 |
| `first_airline_name` | STRING | 第一航段航司名称 |
| `travel_duration_minutes` | INT | 全程时长（分钟） |
| `elapsed_days` | INT | 到达相对出发的跨日数 |
| `is_basic_economy` | BOOLEAN | 是否基础经济舱 |
| `is_refundable` | BOOLEAN | 是否可退 |
| `is_non_stop` | BOOLEAN | 是否直飞 |
| `base_fare` | DECIMAL(12,2) | 基础票价 |
| `total_fare` | DECIMAL(12,2) | 含税总价 |
| `currency` | STRING | 币种，当前为 USD |
| `seats_remaining` | INT | 剩余座位数 |
| `total_distance_miles` | INT | 全程距离（英里），允许为空 |
| `segment_count` | INT | 航段数量 |
| `stop_count` | INT | 中转次数，通常为 `segment_count - 1` |
| `actual_airport_path` | STRING | 实际航段机场路径 |
| `source_file` | STRING | 来源文件 |
| `etl_time` | TIMESTAMP | ETL 处理时间 |
| `search_date` | DATE | 搜索日期，Hive 分区列 |

## 4. `dwd_flight_segments`

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `quote_snapshot_id` | STRING | 关联 `dwd_flight_itinerary.quote_snapshot_id` |
| `leg_id` | STRING | 航程标识 |
| `flight_date` | DATE | 行程出发日期 |
| `segment_index` | INT | 航段序号，从 0 开始 |
| `departure_airport_code` | STRING | 实际出发机场代码 |
| `arrival_airport_code` | STRING | 实际到达机场代码 |
| `departure_time_raw` | STRING | 带时区的原始出发时间 |
| `arrival_time_raw` | STRING | 带时区的原始到达时间 |
| `departure_time_epoch` | BIGINT | 出发 Epoch 秒 |
| `arrival_time_epoch` | BIGINT | 到达 Epoch 秒 |
| `airline_code` | STRING | 执飞航司代码 |
| `airline_name` | STRING | 执飞航司名称 |
| `equipment_description` | STRING | 机型描述，可为空 |
| `duration_seconds` | INT | 航段飞行秒数 |
| `distance_miles` | INT | 航段距离（英里），可为空 |
| `cabin_code` | STRING | 舱位代码 |
| `connection_wait_minutes` | INT | 到下一航段的等待分钟数，末段为空 |
| `source_file` | STRING | 来源文件 |
| `etl_time` | TIMESTAMP | ETL 处理时间 |
| `search_date` | DATE | 搜索日期，Hive 分区列 |

## 5. 航线和拒绝记录

### `dwd_route_info`

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `route_id` | STRING | 市场起点和终点组成的稳定航线标识 |
| `market_origin` | STRING | 市场起点机场代码 |
| `market_destination` | STRING | 市场终点机场代码 |
| `etl_time` | TIMESTAMP | ETL 处理时间 |

### `dwd_itinerary_reject`

字段包括 `source_file`、`source_record_id`、`leg_id`、`raw_search_date`、`error_code`、`error_field`、`error_message`、`raw_record`、`etl_time` 和分区列 `process_date`。该表用于保存可追溯的拒绝原因，不应把拒绝数据重新混入有效事实表。

## 6. 维表和机场能力明细

| 表名 | 主要字段 | 推荐关联方式 |
| --- | --- | --- |
| `dim_airport` | `airport_id`, `ident`, `airport_name`, 经纬度、国家、区域、城市、`iata_code` | 市场机场代码通常关联 `iata_code`；能力表关联 `airport_id`/`ident` |
| `dim_country` | `country_id`, `country_code`, `country_name`, `continent` | `dim_airport.iso_country = dim_country.country_code` |
| `dim_region` | `region_id`, `region_code`, `region_name`, `iso_country` | `dim_airport.iso_region = dim_region.region_code` |
| `dwd_airport_runway` | 跑道尺寸、表面、灯光、关闭状态、两端坐标和方向 | `airport_id` 或 `airport_ident` |
| `dwd_airport_frequency` | 频率类型、描述、`frequency_mhz` | `airport_id` 或 `airport_ident` |
| `dwd_navaid` | 导航台类型、频率、坐标、DME、功率 | `associated_airport_ident = dim_airport.ident`，允许为空 |

维表和机场能力表使用完整小表数据，不受 100 万行事实抽样限制。

## 7. 读取和建模约束

推荐读取：

```python
quotes = (
    spark.table("flight_db.dwd_flight_itinerary")
    .where("search_date = DATE '2022-04-19'")
)
```

算法建模时：

- 预测票价可使用 `total_fare` 作为标签，但必须从输入特征中排除；
- `quote_snapshot_id` 是标识列，不是模型特征；
- 应按日期划分训练/验证数据，不能随机拆分后声称具备时间泛化能力；
- `total_distance_miles`、航段距离和机型等字段允许为空；
- 当前样本日期不均衡，不能直接解释日度趋势。

详细的 Hive、HDFS、PySpark 和 Beeline 读取方法参见 `data_engineering/hive/dwd_hdfs_access.md`。
