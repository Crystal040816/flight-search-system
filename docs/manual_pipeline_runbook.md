# 数据工程手工运维与流水线运行手册

## 1. 使用范围

本手册适用于 `node-master` 上的 Hadoop 3.4.3、Hive 3.1.3、Spark 3.5.3 和 MySQL 8 环境。当前 DWD、DWS、ADS 数据已经验收并冻结；除非存在明确的数据变更需求，本手册中的写入命令不得执行。

数据处理顺序固定为：

```text
ODS -> DWD 小表 -> DWD 行程事实 -> DWS -> MySQL ADS -> 质量验收
```

所有命令默认使用 `hadoop` 用户在 `node-master` 执行。不得在脚本、共享文档或命令历史中写入数据库密码。

## 2. 环境变量

```bash
export JAVA_HOME=/opt/jdk1.8.0_311
export HADOOP_HOME=/opt/hadoop-3.4.3
export HADOOP_CONF_DIR=/opt/hadoop-3.4.3/etc/hadoop
export HIVE_HOME=/opt/apache-hive-3.1.3-bin
export HIVE_CONF_DIR=/opt/apache-hive-3.1.3-bin/conf
export SPARK_HOME=/opt/spark-3.5.3
export PATH="$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$HIVE_HOME/bin:$SPARK_HOME/bin:$PATH"
```

## 3. 服务入口与健康检查

| 服务 | 地址或端口 |
| --- | --- |
| HDFS NameNode | `node-master:9000`，Web UI `9870` |
| YARN ResourceManager | `node-master:8032`，Web UI `8088` |
| Hive Metastore | `node-master:9083` |
| HiveServer2 | `node-master:10000` |
| MySQL ADS | `127.0.0.1:3306/flight_ads` |

只读健康检查：

```bash
jps -l
yarn node -list -all
hdfs dfsadmin -report
hdfs dfsadmin -safemode get
ss -lnt | grep -E ':(9083|10000|3306)[[:space:]]'
mysql --defaults-extra-file="$HOME/.flight_ads_writer.cnf" \
  --batch --skip-column-names -e 'SELECT 1'
```

验收标准为 5 个 YARN 节点 `RUNNING`、5 个 DataNode `Live`、HDFS 安全模式关闭，并且 Hive 与 MySQL 端口可访问。

## 4. 集群启动顺序

1. 启动 5 台虚拟机并确认 `node1` 至 `node4` 可通过 SSH 访问。
2. 在 `node-master` 启动 HDFS：`start-dfs.sh`。
3. 启动 YARN：`start-yarn.sh`。
4. 检查 5 个 DataNode 和 5 个 NodeManager 均已注册。
5. 仅在端口未监听且进程不存在时启动 Hive Metastore 和 HiveServer2。
6. 执行第 3 节的只读健康检查。

不要重复启动 Hive 服务。启动前使用以下命令确认：

```bash
pgrep -af 'proc_metastore|HiveMetaStore'
pgrep -af 'proc_hiveserver2|HiveServer2'
ss -lntp | grep -E ':(9083|10000)[[:space:]]'
```

## 5. 安全停止顺序

1. 确认没有活动的 Spark 或 YARN 应用。
2. 停止对外查询和数据写入任务。
3. 使用已确认的 PID 正常终止 HiveServer2，再终止 Hive Metastore；不要使用模糊的批量 `kill -9`。
4. 执行 `stop-yarn.sh`。
5. 执行 `stop-dfs.sh`。
6. 用 `jps -l` 确认 Hadoop 守护进程已经退出，再关闭各虚拟机。

活动任务检查：

```bash
yarn application -list -appStates SUBMITTED,ACCEPTED,RUNNING
```

## 6. 当前冻结批次的只读验收

```bash
beeline -u 'jdbc:hive2://localhost:10000/flight_db' -e "
SELECT run_id, job_name, COUNT(*) AS check_count,
       SUM(CASE WHEN check_status = 'FAIL' THEN 1 ELSE 0 END) AS failed_checks
FROM dq_check_result
WHERE process_date = DATE '2026-07-21'
GROUP BY run_id, job_name
ORDER BY run_id;
"
```

```bash
mysql --defaults-extra-file="$HOME/.flight_ads_writer.cnf" --table -e "
SELECT 'ads_route_lowest_price' AS table_name, COUNT(*) AS row_count
FROM ads_route_lowest_price
UNION ALL
SELECT 'ads_route_cabin_lowest_price', COUNT(*)
FROM ads_route_cabin_lowest_price
UNION ALL
SELECT 'ads_route_offer_rank', COUNT(*) FROM ads_route_offer_rank
UNION ALL
SELECT 'ads_airline_offer_share', COUNT(*) FROM ads_airline_offer_share;
"
```

这些命令只读取现有数据，不会重新执行 ETL。

## 7. 受控重跑流程

只有获得数据工程负责人确认后才能重跑。必须先执行 `--dry-run`，记录参数和日志，再决定是否写入。

脚本顺序：

```text
spark_etl.py -> itinerary_etl.py -> dws_etl.py -> ads_etl.py
```

关键保护规则：

- `spark_etl.py --dry-run` 只验证小表，不写入。
- `itinerary_etl.py --limit N --dry-run` 只验证样本。
- 使用 `itinerary_etl.py --limit N` 写入时必须显式增加 `--sample-write`。
- `dws_etl.py --dry-run` 不覆盖 DWS。
- `ads_etl.py --dry-run` 不写 MySQL。
- 写入前后都要记录表行数和质量检查 `run_id`。
- 任何 `ERROR + FAIL` 都必须阻止下游发布。

当前正式批次不需要重跑。完整参数以各脚本的 `--help` 和版本库中的源代码为准。

### ADS 2026-07-22 结构升级

本次 ADS 扩展不修改 ODS、DWD 或 DWS。首次发布前，先备份 MySQL `flight_ads`，再执行一次：

```bash
mysql --defaults-extra-file="$HOME/.flight_ads_writer.cnf" \
  < /home/hadoop/flight_project/staging_ads_20260722/ads_schema_upgrade_20260722.sql
```

随后先运行更新后 `ads_etl.py --dry-run`。验证通过且获得写入确认后，才允许正式覆盖 ADS，并执行 `data_engineering/mysql/ads_quality_checks.sql`。升级脚本不能重复执行。

### ADS 2026-07-23 时间字段升级

本次扩展只读取现有 DWD 行程和航段字段，不修改 ODS、DWD 或 DWS。它为两张最低价表增加首航段起飞时间、末航段到达时间、对应 Epoch 秒和整条行程总时长。发布前必须先备份 MySQL `flight_ads`，再执行一次：

```bash
mysql --defaults-extra-file="$HOME/.flight_ads_writer.cnf" \
  < /home/hadoop/flight_project/staging_ads_20260723/ads_schema_upgrade_20260723.sql
```

升级脚本不能重复执行。随后使用新的 HDFS 暂存路径重新计算 ADS，先执行 staged data dry-run，再由 `node-master` 本地 Spark 写入 MySQL。发布后 `09_invalid_route_times` 和 `10_invalid_cabin_times` 必须为 0。

前端需要按不同起飞时刻展示最低价时，在新暂存数据验证通过后、正式发布前执行一次舱型表粒度升级：

```bash
mysql --defaults-extra-file="$HOME/.flight_ads_writer.cnf" \
  < /home/hadoop/flight_project/staging_ads_20260723/ads_schema_upgrade_cabin_time_grain_20260723.sql
```

该脚本会清空尚未更新时间字段的旧舱型表，并把主键改为“搜索日 + 航线 + 出发日 + 起飞 Epoch + 舱型”；因此只能在备份有效且新暂存数据已验证后执行。升级后立即发布新版四表结果。此前按旧粒度生成的暂存结果不得发布。

MySQL 仅监听 `node-master` 的 `127.0.0.1` 时，YARN executor 不能直接使用 JDBC 写入。ADS 发布应拆成两个阶段：先使用 `--stage-output` 在 YARN 上将四张 ADS 结果暂存到 HDFS，再在 `node-master` 使用本地 Spark 和 `--publish-staged` 写入 MySQL。不要为此把 MySQL 暴露到集群网络。

推荐命令形态：

```bash
STAGE_PATH="hdfs:///tmp/flight_ads_release_YYYYMMDD"

spark-submit \
  --master yarn \
  --deploy-mode client \
  --conf spark.network.timeout=600s \
  --conf spark.executor.heartbeatInterval=60s \
  /home/hadoop/flight_project/ads_etl.py \
  --database flight_db \
  --stage-output "$STAGE_PATH"

spark-submit \
  --master 'local[1]' \
  --driver-memory 512m \
  --conf spark.sql.shuffle.partitions=2 \
  /home/hadoop/flight_project/ads_etl.py \
  --mysql-config "$HOME/.flight_ads_writer.cnf" \
  --publish-staged "$STAGE_PATH"
```

第一阶段日志必须出现 `action=staged`，第二阶段必须出现 `action=written target=mysql source=staged`。仅在 MySQL 质量检查通过且备份有效后，才能删除对应 HDFS 暂存目录。

发布后使用以下查询核对四张 ADS 表：

```sql
SELECT 'ads_route_lowest_price' AS table_name, COUNT(*) AS row_count
FROM ads_route_lowest_price
UNION ALL
SELECT 'ads_route_cabin_lowest_price', COUNT(*)
FROM ads_route_cabin_lowest_price
UNION ALL
SELECT 'ads_route_offer_rank', COUNT(*) FROM ads_route_offer_rank
UNION ALL
SELECT 'ads_airline_offer_share', COUNT(*) FROM ads_airline_offer_share;
```

## 8. 常见故障边界

- DataNode 或 NodeManager 数量不足时，只恢复缺失节点，不重建 HDFS。
- HDFS 出现写入告警时先检查 DataNode 日志、磁盘和端口，不删除块目录。
- Hive 表结构以 Metastore 和对应 DDL 为准，不直接移动 HDFS 表目录。
- MySQL 只读用户仅供后端和展示使用，写入账号配置保存在节点本地并设置 `600` 权限。
- `/tmp` 日志不是正式验收依据，最终状态以 `dq_check_result` 和验收报告为准。
- ADS 的 2026-07-22 扩展验收由 `data_engineering/mysql/ads_quality_checks.sql` 对 MySQL 实表执行；它不覆盖 Hive 中 2026-07-21 的基线 `run_id`。
