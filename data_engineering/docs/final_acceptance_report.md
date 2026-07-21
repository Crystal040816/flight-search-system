# 数据工程最终验收报告

## 1. 验收结论

截至 2026-07-21，本项目 ODS、DWD、DWS、ADS 数据链路已完成。DWD、DWS 和 ADS 共 19 项质量检查全部通过，当前批次可用于课程项目展示、后端联调、可视化和算法原型。

当前数据已经冻结。除非数据来源或业务口径发生变化，不需要重新执行写入任务。

## 2. 数据链路

```text
CSV 原始数据
  -> Hive ODS
  -> Spark 清洗与 Hive DWD
  -> Spark 聚合与 Hive DWS
  -> Spark 发布与 MySQL ADS
  -> Hive dq_check_result 记录质量结果
```

## 3. 最终数据规模

| 层级 | 数据对象 | 行数 |
| --- | --- | ---: |
| ODS | `ods_itineraries` | 82,138,753 |
| DWD | `dwd_flight_itinerary` | 1,000,000 |
| DWD | `dwd_flight_segments` | 1,785,428 |
| DWD | `dwd_route_info` | 234 |
| DWD | `dwd_itinerary_reject` | 0 |
| DWD | `dim_country` | 248 |
| DWD | `dim_region` | 3,935 |
| DWD | `dim_airport` | 79,587 |
| DWD | `dwd_airport_runway` | 45,890 |
| DWD | `dwd_airport_frequency` | 29,376 |
| DWD | `dwd_navaid` | 11,020 |
| DWS | `dws_route_daily_stats` | 1,246 |
| DWS | `dws_airline_stats` | 71 |
| DWS | `dws_airport_stats` | 96 |
| DWS | `dws_route_profile` | 234 |
| ADS | `ads_route_lowest_price` | 26,562 |
| ADS | `ads_route_offer_rank` | 1,246 |
| ADS | `ads_airline_offer_share` | 71 |

## 4. 质量验收

| 层级 | `run_id` | 检查数 | 结果 |
| --- | --- | ---: | --- |
| DWD | `dwd_sample_20260721_1014` | 5 | 全部 PASS |
| DWS | `dws_sample_20260721_1100` | 7 | 全部 PASS |
| ADS | `ads_sample_20260721_1142` | 7 | 全部 PASS |

关键结果：

- DWD 报价快照重复数为 0。
- 航段孤儿记录、航段数量不一致和航线孤儿记录均为 0。
- DWS 航线、航司、起点机场和终点机场汇总均守恒至 1,000,000 条报价。
- DWS 非法指标、占比异常和画像孤儿记录均为 0。
- ADS 非法价格、目的地维度缺失、排名断层和航司占比异常均为 0。

正式明细保存在 Hive `flight_db.dq_check_result`，字段和查询方式参见 `../hive/dq_check_result_guide.md`。

## 5. 样本范围与限制

事实数据不是 82,138,753 行 ODS 的全量结果，而是 `FIRST_N_ROWS` 取得的 1,000,000 行教学样本：

- 搜索日期共 6 个，范围为 2022-04-18 至 2022-04-27，日期不连续且分布不均衡。
- 出发日期共 54 个，范围为 2022-04-20 至 2022-06-21。
- 市场航线共 234 条。
- 机场、国家、区域、跑道、频率和导航台使用完整小表数据。

该批次不能用于声明生产模型精度，也不能把报价数量解释为真实销量、客流或市场需求趋势。

## 6. 对外交付

- 算法成员读取 Hive DWD/DWS，或使用 `data_engineering/sample/` 中的 50,000 行 Parquet 样本。
- 后端和展示模块通过 SSH 隧道及 MySQL 只读账号查询 ADS。
- DDL 以 `data_engineering/hive/` 和 `data_engineering/mysql/` 中的版本为准。
- 任何共享材料都不得包含数据库密码或节点本地 `.cnf` 文件内容。

## 7. 冻结与变更控制

当前批次状态为 `ACCEPTED/FROZEN`。后续变更必须使用新的 `run_id`，重新核对各层行数并执行全部质量检查。不得覆盖质量记录或用旧验收结果证明新批次有效。
