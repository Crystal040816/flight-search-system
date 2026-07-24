# 数据工程最终验收报告

## 1. 验收结论

截至 2026-07-22，本项目 ODS、DWD、DWS 和 ADS 数据链路已完成。DWD、DWS 的 2026-07-21 基线验收全部通过；扩展后的 MySQL ADS 于 2026-07-22 完成发布，4 张服务表和 8 项发布后质量指标均通过。

当前数据可用于课程项目展示、后端联调、可视化和算法原型。除非数据来源或业务口径发生变化，不需要重新执行写入任务。

## 2. 数据链路

```text
CSV 原始数据
  -> Hive ODS
  -> Spark 清洗与 Hive DWD
  -> Spark 聚合与 Hive DWS
  -> YARN 计算 ADS 并暂存 HDFS
  -> node-master 本地 Spark 发布 MySQL ADS
  -> Hive 基线质量记录 + MySQL 发布后质量检查
```

MySQL 仅监听 `node-master` 的 `127.0.0.1:3306`。为避免 YARN executor 将回环地址解释为从节点自身，ADS 使用“HDFS 暂存 + node-master 本地发布”的两阶段方式。

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
| ADS | `ads_route_cabin_lowest_price` | 29,587 |
| ADS | `ads_route_offer_rank` | 1,246 |
| ADS | `ads_airline_offer_share` | 71 |

## 4. 质量验收

### 4.1 Hive 基线验收

| 层级 | `run_id` | 检查数 | 结果 |
| --- | --- | ---: | --- |
| DWD | `dwd_sample_20260721_1014` | 5 | 全部 PASS |
| DWS | `dws_sample_20260721_1100` | 7 | 全部 PASS |
| ADS 基线 | `ads_sample_20260721_1142` | 7 | 全部 PASS |

以上 19 项正式摘要保存在 Hive `flight_db.dq_check_result`，字段和查询方式参见 [质量检查与 Hive 质量表说明](../data_engineering/hive/dq_check_result_guide.md)。

### 4.2 ADS 扩展发布验收

2026-07-22 使用 `data_engineering/mysql/ads_quality_checks.sql` 对发布后的 MySQL 实表执行只读检查：

| 指标 | 结果 |
| --- | ---: |
| 最低价表行数 | 26,562 |
| 舱型最低价表行数 | 29,587 |
| 非法价格或座位数 | 0 |
| 缺失出发地维度 | 0 |
| 缺失目的地维度 | 0 |
| 非法舱型指标 | 0 |
| 重复舱型粒度 | 0 |
| 最低价报价未进入舱型表 | 0 |

本次扩展检查是 MySQL 发布后验收，不冒充或覆盖 2026-07-21 的 Hive `run_id`。

## 5. ADS 交付范围

最低价服务表已提供：

- 出发地和目的地机场代码、城市、国家；
- 出发日期、最低含税总价、平均价和币种；
- 首段航司、剩余座位；
- 舱型类别、逐航段舱型、混合舱型标识；
- 逐航段机型描述；
- 同一航线与日期下按舱型比较最低价。

当前口径是“样本报价中的最低价”，允许出现 `seats_remaining=0` 的历史报价，展示时应标记无余票，不能称为“最低可购买价”。`airline_name` 表示首段航司。原始数据没有航班号和航站楼，ADS 不伪造这两个字段。

## 6. 样本范围与限制

事实数据不是 82,138,753 行 ODS 的全量结果，而是 `FIRST_N_ROWS` 取得的 1,000,000 行教学样本：

- 搜索日期共 6 个，范围为 2022-04-18 至 2022-04-27，日期不连续且分布不均衡；
- 出发日期共 54 个，范围为 2022-04-20 至 2022-06-21；
- 市场航线共 234 条；
- 机场、国家、区域、跑道、频率和导航台使用完整小表数据。

该批次不能用于声明生产模型精度，也不能把报价数量解释为真实销量、客流或市场需求趋势。

## 7. 对外交付

- 算法成员读取 Hive DWD/DWS，或使用 `data_engineering/sample/` 中的 Parquet 样本；
- 后端和展示模块通过 SSH 隧道及 MySQL 只读账号查询 ADS；
- DDL 以 `data_engineering/hive/` 和 `data_engineering/mysql/` 中的版本为准；
- 业务字段口径以 [ADS 数据字典](ads_data_dictionary.md) 为准；
- 任何共享材料都不得包含数据库密码或节点本地 `.cnf` 文件内容。

## 8. 冻结与变更控制

当前 DWD/DWS 基线和 2026-07-22 ADS 发布状态为 `ACCEPTED/FROZEN`。后续变更必须先备份、执行 dry-run、使用新的验收标识并重新核对对应层行数。不得覆盖旧质量记录或用旧验收结果证明新数据有效。
