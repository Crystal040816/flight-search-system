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

## 8. 常见故障边界

- DataNode 或 NodeManager 数量不足时，只恢复缺失节点，不重建 HDFS。
- HDFS 出现写入告警时先检查 DataNode 日志、磁盘和端口，不删除块目录。
- Hive 表结构以 Metastore 和对应 DDL 为准，不直接移动 HDFS 表目录。
- MySQL 只读用户仅供后端和展示使用，写入账号配置保存在节点本地并设置 `600` 权限。
- `/tmp` 日志不是正式验收依据，最终状态以 `dq_check_result` 和验收报告为准。
