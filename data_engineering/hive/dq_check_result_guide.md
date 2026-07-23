# 质量检查与 Hive 质量表说明

## 1. 文档用途

本项目使用 Hive 表 `flight_db.dq_check_result` 统一保存 ODS、DWD、DWS 和 ADS
各阶段的数据质量检查结果。该表保存的是检查摘要，不保存业务明细数据。

建议将本文档提供给以下成员：

- 数据工程成员：确认 ETL 是否可以进入下一层。
- 算法成员：确认训练或分析使用的数据批次已经通过质量检查。
- 后端成员：确认 API 依赖的 ADS 数据是否可用。
- 项目维护者：将质量检查作为进入下一层或对外发布的失败门禁。
- Superset 使用者：了解展示数据的样本范围及限制。

只共享读取方式，不应向算法、后端或可视化账号授予 Hive/HDFS 写权限。

## 2. 表位置与格式

Hive 表名：

```text
flight_db.dq_check_result
```

数据格式：

```text
Parquet + Snappy
```

分区字段：

```text
process_date DATE
```

默认 HDFS 目录通常为：

```text
hdfs://node-master:9000/user/hive/warehouse/flight_db.db/dq_check_result
```

实际位置以 Hive Metastore 为准：

```bash
beeline -u 'jdbc:hive2://localhost:10000/flight_db' \
  -e 'DESCRIBE FORMATTED dq_check_result;'
```

查看输出中的 `Location` 字段。Parquet 是二进制格式，不要使用
`hdfs dfs -cat` 读取质量表文件。

## 3. 字段说明

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `run_id` | STRING | 一次质量检查批次的唯一标识 |
| `job_name` | STRING | 产生该检查结果的 ETL 或验收任务 |
| `check_code` | STRING | 稳定的检查代码，供程序和自动化检查判断 |
| `check_name` | STRING | 面向人员阅读的检查名称 |
| `check_level` | STRING | `ERROR` 或 `WARN` |
| `check_status` | STRING | `PASS` 或 `FAIL` |
| `input_count` | BIGINT | 本项检查涉及的输入记录数 |
| `failed_count` | BIGINT | 未通过检查的记录数或对象数 |
| `failure_rate` | DECIMAL(12,8) | `failed_count / input_count` |
| `threshold_value` | STRING | 允许阈值或预期值 |
| `details` | STRING | 数据范围、目标位置或实际指标摘要 |
| `started_at` | TIMESTAMP | 检查开始时间 |
| `finished_at` | TIMESTAMP | 检查结束时间 |
| `process_date` | DATE | Hive 分区日期 |

`failure_rate` 为 0 到 1 的比例，不是百分数。检查程序不能只依赖中文
`check_name`，应使用稳定的 `check_code`。

## 4. 当前数据范围

机场、国家、区域、跑道、频率和导航台使用全量数据。行程事实数据使用教学样本：

```text
原始 ODS 行程记录：82,138,753
DWD 报价样本：       1,000,000
DWD 航段记录：       1,785,428
抽样方式：            FIRST_N_ROWS
搜索日期数：          6
市场航线数：          234
```

该样本不是随机或按日期均衡抽样。日度报价数量差异不能解释为真实商业供给
趋势，模型评估结果也不能表述为生产精度。

## 5. 当前验收批次

### 5.1 DWD 验收

```text
run_id:   dwd_sample_20260721_1014
job_name: dwd_sample_validation
```

| 检查代码 | 结果 | 主要指标 |
| --- | --- | --- |
| `DWD_ROW_COUNT` | PASS | 报价 1,000,000 行 |
| `DWD_SNAPSHOT_UNIQUE` | PASS | 重复快照 ID 为 0 |
| `DWD_SEGMENT_FK` | PASS | 航段孤儿报价为 0 |
| `DWD_SEGMENT_COUNT` | PASS | 航段数量不一致为 0 |
| `DWD_ROUTE_FK` | PASS | 航线孤儿记录为 0 |

### 5.2 DWS 验收

```text
run_id:   dws_sample_20260721_1100
job_name: dws_sample_validation
```

| 检查代码 | 结果 | 主要指标 |
| --- | --- | --- |
| `DWS_ROUTE_CONSERVATION` | PASS | 航线报价合计 1,000,000 |
| `DWS_AIRLINE_CONSERVATION` | PASS | 航司报价合计 1,000,000 |
| `DWS_AIRPORT_ORIGIN` | PASS | 起点报价合计 1,000,000 |
| `DWS_AIRPORT_DESTINATION` | PASS | 终点报价合计 1,000,000 |
| `DWS_ROUTE_METRICS` | PASS | 无非法价格或直飞率 |
| `DWS_AIRLINE_SHARE` | PASS | 各搜索日航司占比合计为 100 |
| `DWS_ROUTE_PROFILE_FK` | PASS | 航线画像孤儿记录为 0 |

当前 DWS 行数：

```text
dws_route_daily_stats: 1,246
dws_airline_stats:        71
dws_airport_stats:        96
dws_route_profile:       234
```

### 5.3 ADS 基线验收

```text
run_id:   ads_sample_20260721_1142
job_name: ads_mysql_validation
target:   MySQL flight_ads
```

| 检查代码 | 结果 | 主要指标 |
| --- | --- | --- |
| `ADS_LOWEST_ROWS` | PASS | 最低价结果 26,562 行 |
| `ADS_ROUTE_RANK_ROWS` | PASS | 航线排行 1,246 行 |
| `ADS_AIRLINE_SHARE_ROWS` | PASS | 航司占比 71 行 |
| `ADS_PRICE_VALIDITY` | PASS | 非法最低价为 0 |
| `ADS_DESTINATION_DIMENSION` | PASS | 目的地维度缺失为 0 |
| `ADS_RANK_CONTINUITY` | PASS | 排名异常日期为 0 |
| `ADS_AIRLINE_SHARE` | PASS | 占比异常日期为 0 |

ADS 业务结果存放在 MySQL `flight_ads` 数据库；ADS 质量摘要仍写入 Hive
`flight_db.dq_check_result`，以便统一判断整个数据链路。

### 5.4 ADS 2026-07-22 扩展发布验收

本次扩展增加出发地维度、剩余座位、舱型与机型，并新增
`ads_route_cabin_lowest_price`。发布后使用
`data_engineering/mysql/ads_quality_checks.sql` 直接检查 MySQL 实表：

| 指标 | 结果 | 主要指标 |
| --- | --- | --- |
| `01_lowest_price_rows` | PASS | 26,562 行 |
| `02_cabin_lowest_price_rows` | PASS | 29,587 行 |
| `03_invalid_price_or_seats` | PASS | 失败数 0 |
| `04_missing_origin_dimensions` | PASS | 失败数 0 |
| `05_missing_destination_dimensions` | PASS | 失败数 0 |
| `06_invalid_cabin_metrics` | PASS | 失败数 0 |
| `07_duplicate_cabin_grain` | PASS | 失败数 0 |
| `08_lowest_quote_missing_from_cabin_table` | PASS | 失败数 0 |

这 8 项是 2026-07-22 的 MySQL 发布后验收结果，不属于
`ads_sample_20260721_1142`，也没有修改 Hive 中已有的 7 项 ADS 基线记录。

## 6. 常用查询

查询某个批次的全部检查：

```sql
SELECT
    run_id,
    job_name,
    check_code,
    check_level,
    check_status,
    input_count,
    failed_count,
    failure_rate,
    threshold_value,
    details
FROM flight_db.dq_check_result
WHERE process_date = DATE '2026-07-21'
  AND run_id = 'dwd_sample_20260721_1014'
ORDER BY check_code;
```

汇总当天各批次状态：

```sql
SELECT
    process_date,
    run_id,
    job_name,
    COUNT(*) AS check_count,
    SUM(CASE WHEN check_status = 'FAIL' THEN 1 ELSE 0 END) AS failed_checks
FROM flight_db.dq_check_result
WHERE process_date = DATE '2026-07-21'
GROUP BY process_date, run_id, job_name
ORDER BY run_id;
```

查询所有阻断级失败：

```sql
SELECT *
FROM flight_db.dq_check_result
WHERE check_level = 'ERROR'
  AND check_status = 'FAIL'
ORDER BY process_date DESC, finished_at DESC;
```

通过 PySpark 读取：

```python
checks = (
    spark.table("flight_db.dq_check_result")
    .where("process_date = DATE '2026-07-21'")
)

checks.orderBy("run_id", "check_code").show(truncate=False)
```

## 7. 质量门禁规则

推荐采用以下规则：

1. 上游 ETL 成功后才执行质量检查。
2. 预期 `check_code` 必须全部存在，不能仅判断现有行是否都是 `PASS`。
3. 任意 `ERROR + FAIL` 阻止下游任务。
4. `WARN + FAIL` 可以继续，但必须在任务日志或验收报告中记录。
5. 缺少质量批次、检查项数量不足或批次重复时，按失败处理。
6. ADS 发布完成后再执行 MySQL 侧质量检查，不能只验证 Spark DataFrame。

伪代码：

```python
expected_checks = {
    "DWD_ROW_COUNT",
    "DWD_SNAPSHOT_UNIQUE",
    "DWD_SEGMENT_FK",
    "DWD_SEGMENT_COUNT",
    "DWD_ROUTE_FK",
}

actual_checks = {row.check_code for row in rows}
if actual_checks != expected_checks:
    raise ValueError("Missing or unexpected DQ checks")

if any(
    row.check_level == "ERROR" and row.check_status == "FAIL"
    for row in rows
):
    raise ValueError("Blocking data quality check failed")
```

当前批次由人工命令写入。后续无论使用脚本还是其他执行器，都必须生成唯一
`run_id`、执行检查并写入质量表，避免手工维护常量。

## 8. 日志与正式报告的区别

`node-master` 上的以下文件是运行过程日志：

```text
/tmp/dwd-final-validation.log
/tmp/dwd-dq-result-write.log
/tmp/dws-final-validation.log
/tmp/dws-dq-result-write.log
/tmp/ads-etl-mysql-write.log
/tmp/ads-dq-result-write.log
```

2026-07-22 的 ADS 发布采用 HDFS 暂存后本地写入 MySQL，运行日志默认保存在
`/home/hadoop/flight_project/`。日志仅用于排障，最终结论以 MySQL 质量检查输出和
`docs/final_acceptance_report.md` 为准。

`/tmp` 可能在重启或系统清理后被删除，不能作为唯一验收依据。正式状态以
Hive `dq_check_result` 中的批次记录为准。需要归档日志时，应复制到：

```text
/home/hadoop/flight_project/reports/
```

不要在共享文档中记录 MySQL 密码、Hive 密码或 `.cnf` 文件内容。

## 9. 使用约束

- 不要手工修改已有 `PASS` 或 `FAIL` 记录。
- 重跑任务时使用新的 `run_id`，不要复用旧批次冒充最新结果。
- 业务数据更新后必须重新执行对应层的质量检查。
- 算法和后端读取数据前，应记录所使用的 `run_id` 和数据范围。
- Superset 只读取 MySQL ADS，不直接依赖 Hive 质量表；验收报告或运维页面负责
  展示质量门禁状态。
