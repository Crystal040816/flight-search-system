# DWD 层 HDFS 访问说明

## 1. 存储位置

DWD 层由 Hive 管理，数据文件采用 Parquet 格式并使用 Snappy 压缩。当前数据库的默认 HDFS 目录为：

```text
hdfs://node-master:9000/user/hive/warehouse/flight_db.db
```

在已经配置 `fs.defaultFS` 的集群节点上，可使用简写：

```text
/user/hive/warehouse/flight_db.db
```

Hive Metastore 中登记的 `Location` 是最终事实。读取前可核对单表实际路径：

```bash
beeline -u 'jdbc:hive2://localhost:10000/flight_db' \
  -e 'DESCRIBE FORMATTED dwd_flight_itinerary;'
```

查看输出中的 `Location` 字段。不要仅根据目录名猜测表位置。

## 2. DWD 表与目录

| Hive 表 | 默认 HDFS 目录 | 分区 | 说明 |
| --- | --- | --- | --- |
| `dwd_flight_itinerary` | `flight_db.db/dwd_flight_itinerary` | `search_date` | 报价快照，一条有效报价一行 |
| `dwd_flight_segments` | `flight_db.db/dwd_flight_segments` | `search_date` | 航段明细，一条报价对应一到多个航段 |
| `dim_airport` | `flight_db.db/dim_airport` | 无 | 机场维表 |
| `dim_country` | `flight_db.db/dim_country` | 无 | 国家维表 |
| `dim_region` | `flight_db.db/dim_region` | 无 | 区域维表 |
| `dwd_airport_runway` | `flight_db.db/dwd_airport_runway` | 无 | 机场跑道明细 |
| `dwd_airport_frequency` | `flight_db.db/dwd_airport_frequency` | 无 | 机场通信频率明细 |
| `dwd_navaid` | `flight_db.db/dwd_navaid` | 无 | 导航台明细 |
| `dwd_route_info` | `flight_db.db/dwd_route_info` | 无 | 市场航线基础信息 |
| `dwd_itinerary_reject` | `flight_db.db/dwd_itinerary_reject` | `process_date` | ETL 拒绝记录 |
| `dq_check_result` | `flight_db.db/dq_check_result` | `process_date` | 数据质量检查结果 |

完整字段名、类型、顺序和注释参见同目录下的 `dwd_ddl.sql`。

## 3. 当前数据范围

机场相关的 6 张小表使用全量数据：

| 表 | 当前行数 |
| --- | ---: |
| `dim_country` | 248 |
| `dim_region` | 3,935 |
| `dim_airport` | 79,587 |
| `dwd_airport_runway` | 45,890 |
| `dwd_airport_frequency` | 29,376 |
| `dwd_navaid` | 11,020 |

行程事实数据采用教学实验样本：

- `dwd_flight_itinerary`：1,000,000 行。
- 原始 ODS 行程数据：82,138,753 行。
- 抽样方式：`FIRST_N_ROWS`，不是随机或均衡抽样。
- 搜索日期：6 个，范围为 `2022-04-18` 至 `2022-04-27`。
- 搜索日期并不连续，且每天样本量不同。
- 航线覆盖：234 条市场航线。
- 拒绝记录：本次样本 ETL 为 0 行。

该数据适合开发、联调和学生项目演示。不得将日度报价数量差异解释为真实商业供给趋势，也不得用于生产模型精度声明。

## 4. 推荐读取方式：通过 Hive Metastore

算法和批处理任务优先通过 Hive 表名读取。这样可以自动获得 Schema、分区列和表位置。

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("read-flight-dwd")
    .enableHiveSupport()
    .getOrCreate()
)

quotes = (
    spark.table("flight_db.dwd_flight_itinerary")
    .where("search_date = DATE '2022-04-19'")
)

quotes.printSchema()
quotes.show(20, truncate=False)
print(quotes.count())
```

在 `node-master` 提交：

```bash
/opt/spark-3.5.3/bin/spark-submit \
  --master yarn \
  --deploy-mode client \
  read_dwd.py
```

集群已配置：

```text
Hive Metastore: thrift://node-master:9083
HiveServer2:     jdbc:hive2://node-master:10000/flight_db
HDFS NameNode:  hdfs://node-master:9000
```

如果在新的 Spark 客户端运行，应复制集群的 `core-site.xml`、`hdfs-site.xml` 和 `hive-site.xml`，并确保客户端能解析 `node-master` 和访问对应端口。

## 5. 直接通过 HDFS 读取 Parquet

不使用 Hive Metastore 时，可以直接读取表目录。外部客户端建议使用完整 HDFS URI。

读取整张非分区表：

```python
airports = spark.read.parquet(
    "hdfs://node-master:9000/user/hive/warehouse/flight_db.db/dim_airport"
)
```

读取整张分区表：

```python
root = (
    "hdfs://node-master:9000/user/hive/warehouse/"
    "flight_db.db/dwd_flight_itinerary"
)

quotes = spark.read.option("basePath", root).parquet(root)
```

只读取一个搜索日期分区：

```python
root = (
    "hdfs://node-master:9000/user/hive/warehouse/"
    "flight_db.db/dwd_flight_itinerary"
)

quotes = (
    spark.read
    .option("basePath", root)
    .parquet(f"{root}/search_date=2022-04-19")
)
```

设置 `basePath` 可以让 Spark 从目录名恢复 `search_date` 分区列。

## 6. HDFS 检查命令

查看数据库目录：

```bash
hdfs dfs -ls /user/hive/warehouse/flight_db.db
```

查看表大小和文件：

```bash
hdfs dfs -du -h \
  /user/hive/warehouse/flight_db.db/dwd_flight_itinerary

hdfs dfs -ls -h \
  /user/hive/warehouse/flight_db.db/dwd_flight_itinerary
```

查看分区目录：

```bash
hdfs dfs -ls \
  /user/hive/warehouse/flight_db.db/dwd_flight_itinerary/search_date=*
```

检查 HDFS 健康状态：

```bash
hdfs fsck \
  /user/hive/warehouse/flight_db.db/dwd_flight_itinerary \
  -files -blocks -locations
```

Parquet 是二进制格式，不要使用 `hdfs dfs -cat` 查看内容。应使用 Spark、Hive、PyArrow 或其他 Parquet 读取器。

## 7. Beeline 查询

适合查看 Schema、样例和小型聚合，不适合将百万行明细下载到客户端。

```bash
beeline -u 'jdbc:hive2://localhost:10000/flight_db' \
  -e "
SELECT
    search_date,
    COUNT(*) AS quote_count,
    MIN(total_fare) AS min_fare,
    AVG(total_fare) AS avg_fare
FROM dwd_flight_itinerary
GROUP BY search_date
ORDER BY search_date;
"
```

## 8. 访问要求

直接访问 HDFS 的人员或服务需要：

1. 能访问 `node-master:9000`。
2. 能解析 `node-master`、`node1` 至 `node4`，或配置对应 hosts/DNS。
3. 使用与集群兼容的 Hadoop/Spark 客户端。
4. 具备 HDFS 目录读取权限。
5. 通过 Hive 读取时，还需访问 Metastore `9083`；通过 JDBC 查询时需访问 HiveServer2 `10000`。

可以检查当前权限：

```bash
hdfs dfs -ls -d /user/hive/warehouse/flight_db.db
hdfs dfs -ls /user/hive/warehouse/flight_db.db
```

## 9. 禁止操作

- 不要直接删除、移动或重命名 Hive 管理目录。
- 不要手动向分区目录复制格式不一致的文件。
- 不要在 HDFS 表目录中创建临时文本文件。
- 不要绕过 ETL 修改 DWD 数据。
- 不要将 HDFS 写权限共享给只需要读取数据的算法或展示模块。

需要更新数据时，应按运行手册执行对应 Spark ETL，并由 Hive Metastore 管理表和分区。

## 10. 面向不同模块的接口

- 算法开发：优先读取 DWD/DWS Hive 表；本地开发使用 `data_engineering/sample/dwd_sample.parquet`。
- DWS 聚合：通过 Spark 读取 DWD 表，并按 `search_date` 增量处理。
- ADS：读取 DWS 和算法结果，最终写入 MySQL。
- Superset/后端：读取 MySQL ADS，不直接扫描 HDFS DWD 明细。

生产式算法接口建议由算法模块生成稳定的特征表，避免算法代码长期依赖多个 DWD 物理目录。
