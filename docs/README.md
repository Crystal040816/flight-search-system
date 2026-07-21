# 数据工程交付文档索引

## 1. 当前数据链路

```text
CSV 原始文件
  -> Hive ODS（外部表、原始字符串）
  -> Hive DWD（清洗后的明细与维表）
  -> Hive DWS（按搜索日期汇总的统计表）
  -> MySQL ADS（供后端和可视化直接查询）
```

数据库与服务入口：

| 服务 | 入口 | 用途 |
| --- | --- | --- |
| Hive 数据库 | `flight_db` | ODS、DWD、DWS 和质量结果 |
| Hive Metastore | `thrift://node-master:9083` | Spark 获取 Hive Schema 和表位置 |
| HiveServer2 | `jdbc:hive2://node-master:10000/flight_db` | Beeline/JDBC 查询 |
| HDFS | `hdfs://node-master:9000` | ODS、DWD、DWS 物理数据 |
| MySQL | `127.0.0.1:3306/flight_ads` | ADS 服务层，仅在 `node-master` 本机访问 |

## 2. 文档清单

| 文档 | 主要读者 | 内容 |
| --- | --- | --- |
| [ODS 数据字典](ods_data_dictionary.md) | 数据工程成员 | 原始表、字段、HDFS 位置和只读约束 |
| [DWD 数据字典](dwd_data_dictionary.md) | 算法、数据工程成员 | 明细粒度、关联键、样本范围和字段口径 |
| [DWS 数据字典](dws_data_dictionary.md) | 算法、分析成员 | 日度汇总指标及统计口径 |
| [ADS 数据字典](ads_data_dictionary.md) | 后端、Superset、展示成员 | MySQL 表、主键、指标语义和查询示例 |
| [DWD HDFS 读取说明](../hive/dwd_hdfs_access.md) | 算法成员 | Spark/Hive/HDFS 读取方式 |
| [质量检查与 Hive 质量表说明](../hive/dq_check_result_guide.md) | 全体成员 | DWD/DWS/ADS 验收结果和质量门禁 |

DDL 是最终结构依据：

- ODS：`data_engineering/hive/ods_ddl.sql`
- DWD：`data_engineering/hive/dwd_ddl.sql`
- DWS：`data_engineering/hive/dws_ddl.sql`
- ADS 逻辑结构：`data_engineering/hive/ads_ddl.sql`
- ADS MySQL 结构：`data_engineering/mysql/ads_ddl.sql`

## 3. 当前数据批次

| 数据对象 | 当前规模 |
| --- | ---: |
| ODS 原始行程报价 | 82,138,753 |
| DWD 报价快照 | 1,000,000 |
| DWD 航段 | 1,785,428 |
| DWD 航线 | 234 |
| DWS 航线日统计 | 1,246 |
| DWS 航司日统计 | 71 |
| DWS 机场日统计 | 96 |
| DWS 航线画像 | 234 |
| ADS 最低价 | 26,562 |
| ADS 航线排行 | 1,246 |
| ADS 航司报价占比 | 71 |

事实数据采用 `FIRST_N_ROWS` 从 82,138,753 条 ODS 数据中选取 1,000,000 条，不是随机抽样，也不是按日期均衡抽样。当前样本包含 6 个不连续搜索日期，搜索日期范围为 2022-04-18 至 2022-04-27，出发日期范围为 2022-04-20 至 2022-06-21。

因此，该批次适合课程项目、接口联调、功能演示和算法原型，不适合声明生产模型精度，也不能把报价数量解释为真实销量、客流或市场需求。

## 4. 模块读取边界

| 模块 | 推荐读取层 | 原因 |
| --- | --- | --- |
| 数据工程 | ODS、DWD、DWS、质量表 | 负责 ETL、核对与重跑 |
| 算法 | DWD、DWS | 需要明细特征或稳定聚合特征 |
| 后端 API | MySQL ADS | 查询延迟低，结构和索引稳定 |
| Superset | MySQL ADS | 避免扫描 HDFS 百万行明细 |
| 项目验收 | `dq_check_result` | 追溯每层质量检查批次 |

非数据工程成员原则上只获得读取权限。不要直接删除、移动或覆盖 Hive/HDFS 表目录，也不要绕过 ETL 修改 DWD/DWS。ADS 账号应按用途创建只读用户，不共享写入账号或密码文件。

## 5. Airflow 与现有数据的关系

Airflow 只负责按依赖顺序调用已经验证的 Spark ETL 和校验命令。当前项目 DAG 为 `flight_sample_batch_pipeline`，保持暂停且 `schedule=None`，不会自动重跑或修改现有数据。

只有在以下动作同时发生时，Airflow 才会执行项目 ETL：

1. Airflow 调度服务正在运行；
2. 项目 DAG 被解除暂停；
3. 用户手动触发该 DAG。

清理 Airflow 官方示例 DAG 的元数据不会删除 Hive、HDFS、MySQL 数据，也不会影响项目源代码。
