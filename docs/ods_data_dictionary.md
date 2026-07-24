# ODS 数据字典与使用说明

## 1. 层级定位

ODS 保存源 CSV 的原始内容，用于追溯和重新清洗。所有业务列按 `STRING` 接入，不在 ODS 做类型转换、去重或业务校验。

- Hive 数据库：`flight_db`
- 表类型：外部表
- 文件格式：CSV/TextFile
- CSV 解析：`OpenCSVSerde`
- 首行：通过 `skip.header.line.count=1` 跳过
- 写入责任：仅数据工程 ETL/导入任务
- 下游：DWD Spark ETL

ODS 表不代表清洗后的可信业务数据。算法、后端和可视化模块不应直接依赖 ODS。

## 2. 表清单

| 表名 | 粒度 | 主要用途 | HDFS 位置 |
| --- | --- | --- | --- |
| `ods_itineraries` | 一条原始搜索报价记录 | 行程和航段清洗来源 | `/user/hive/warehouse/flight_db/ods_itineraries` |
| `ods_airports` | 一个原始机场 | 机场维表来源 | `/user/hive/warehouse/flight_db/ods_airports` |
| `ods_runways` | 一条原始跑道 | 跑道明细来源 | `/user/hive/warehouse/flight_db/ods_runways` |
| `ods_airport_frequencies` | 一条机场频率 | 机场频率明细来源 | `/user/hive/warehouse/flight_db/ods_airport_frequencies` |
| `ods_countries` | 一个国家/地区 | 国家维表来源 | `/user/hive/warehouse/flight_db/ods_countries` |
| `ods_regions` | 一个行政区域 | 区域维表来源 | `/user/hive/warehouse/flight_db/ods_regions` |
| `ods_navaids` | 一个导航台 | 导航台明细来源 | `/user/hive/warehouse/flight_db/ods_navaids` |

## 3. `ods_itineraries`

该表共有 27 个字符串字段。`legId` 是航程标识，但同一个航程可能在不同搜索日期或报价条件下重复出现，不能把它单独作为报价唯一键。

| 字段 | 含义 |
| --- | --- |
| `legId` | 航程标识 |
| `searchDate` | 用户搜索日期 |
| `flightDate` | 行程出发日期 |
| `startingAirport` | 搜索起点市场机场 IATA 代码 |
| `destinationAirport` | 搜索终点市场机场 IATA 代码 |
| `fareBasisCode` | 票价基础代码 |
| `travelDuration` | ISO-8601 格式的全程时长 |
| `elapsedDays` | 到达相对出发的跨日数 |
| `isBasicEconomy` | 是否基础经济舱，原始字符串 |
| `isRefundable` | 是否可退，原始字符串 |
| `isNonStop` | 是否直飞，原始字符串 |
| `baseFare` | 基础票价，原始字符串 |
| `totalFare` | 含税总价，原始字符串 |
| `seatsRemaining` | 剩余座位数，原始字符串 |
| `totalTravelDistance` | 全程距离（英里），可为空 |
| `segmentsDepartureTimeEpochSeconds` | 各航段出发 Epoch 秒，以 `||` 分隔 |
| `segmentsDepartureTimeRaw` | 各航段原始出发时间，以 `||` 分隔 |
| `segmentsArrivalTimeEpochSeconds` | 各航段到达 Epoch 秒，以 `||` 分隔 |
| `segmentsArrivalTimeRaw` | 各航段原始到达时间，以 `||` 分隔 |
| `segmentsArrivalAirportCode` | 各航段实际到达机场代码，以 `||` 分隔 |
| `segmentsDepartureAirportCode` | 各航段实际出发机场代码，以 `||` 分隔 |
| `segmentsAirlineName` | 各航段航司名称，以 `||` 分隔 |
| `segmentsAirlineCode` | 各航段航司代码，以 `||` 分隔 |
| `segmentsEquipmentDescription` | 各航段机型描述，以 `||` 分隔，可为空 |
| `segmentsDurationInSeconds` | 各航段飞行秒数，以 `||` 分隔 |
| `segmentsDistance` | 各航段距离（英里），以 `||` 分隔 |
| `segmentsCabinCode` | 各航段舱位代码，以 `||` 分隔 |

所有 `segments*` 数组必须在 DWD 清洗时验证长度一致，再展开为 `dwd_flight_segments`。不能直接按字符串位置假设航段有效。

## 4. 机场基础数据表

### `ods_airports`

字段：`id`、`ident`、`type`、`name`、`latitude_deg`、`longitude_deg`、`elevation_ft`、`continent`、`iso_country`、`iso_region`、`municipality`、`scheduled_service`、`gps_code`、`iata_code`、`local_code`、`home_link`、`wikipedia_link`、`keywords`。

### `ods_runways`

字段：`id`、`airport_ref`、`airport_ident`、`length_ft`、`width_ft`、`surface`、`lighted`、`closed`、`le_ident`、`le_latitude_deg`、`le_longitude_deg`、`le_elevation_ft`、`le_heading_degT`、`le_displaced_threshold_ft`、`he_ident`、`he_latitude_deg`、`he_longitude_deg`、`he_elevation_ft`、`he_heading_degT`、`he_displaced_threshold_ft`。

`le_*` 和 `he_*` 分别描述跑道低端和高端。

### `ods_airport_frequencies`

字段：`id`、`airport_ref`、`airport_ident`、`type`、`description`、`frequency_mhz`。

### `ods_countries`

字段：`id`、`code`、`name`、`continent`、`wikipedia_link`、`keywords`。

### `ods_regions`

字段：`id`、`code`、`local_code`、`name`、`continent`、`iso_country`、`wikipedia_link`、`keywords`。

### `ods_navaids`

字段：`id`、`filename`、`ident`、`name`、`type`、`frequency_khz`、`latitude_deg`、`longitude_deg`、`elevation_ft`、`iso_country`、`dme_frequency_khz`、`dme_channel`、`dme_latitude_deg`、`dme_longitude_deg`、`dme_elevation_ft`、`slaved_variation_deg`、`magnetic_variation_deg`、`usageType`、`power`、`associated_airport`。

## 5. 推荐检查与查询

```sql
SELECT COUNT(*) FROM flight_db.ods_itineraries;

SELECT *
FROM flight_db.ods_airports
LIMIT 10;
```

查看物理位置时以 Hive Metastore 为准：

```bash
beeline -u 'jdbc:hive2://localhost:10000/flight_db' \
  -e 'DESCRIBE FORMATTED ods_itineraries;'
```

禁止直接修改 ODS 目录中的单个文件。需要替换源数据时，应保留来源、文件校验值和导入批次，并重新运行下游 DWD、DWS、ADS 及质量检查。
