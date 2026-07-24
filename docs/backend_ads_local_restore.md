# 后端本地 ADS 恢复说明

## 1. 交付内容

后端交付目录包含：

- `flight_ads_20260724.sql.gz`：MySQL ADS 四张表的结构和数据；
- `flight_ads_20260724.sql.gz.sha256`：归档文件 SHA-256；
- `BACKUP_MANIFEST.txt`：数据库版本、表数量和验收行数；
- `README_BACKEND_RESTORE.md`：本文档副本。

归档文件的预期 SHA-256：

```text
c084adb15d10db9793ff44caa8de5fd041fdd4b34541fb073ab7616890c211eb
```

该备份是 2026-07-24 的 `flight_ads` 时间点副本，恢复过程不会读取 DWS，也不需要 Hadoop、Hive 或 Spark。备份不包含数据库用户、密码、存储过程、触发器或事件。

## 2. 环境要求

- MySQL 8.0；
- 建议至少预留 1 GB 可用磁盘空间；
- 使用能够创建数据库和本地只读账号的 MySQL 管理账号。

前端不得直接连接 MySQL。调用关系应为：本地 MySQL ADS -> 后端 API -> 前端。

## 3. 校验归档

Windows PowerShell：

```powershell
$Archive = ".\flight_ads_20260724.sql.gz"
$Expected = "c084adb15d10db9793ff44caa8de5fd041fdd4b34541fb073ab7616890c211eb"
$Actual = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLower()
if ($Actual -ne $Expected) { throw "ADS 备份 SHA-256 校验失败" }
Write-Host "ads_backup_verified=PASS"
```

Linux：

```bash
sha256sum -c flight_ads_20260724.sql.gz.sha256
gzip -t flight_ads_20260724.sql.gz
```

## 4. 创建数据库

登录本地 MySQL：

```bash
mysql -u root -p
```

执行：

```sql
CREATE DATABASE IF NOT EXISTS flight_ads
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
```

## 5. 导入数据

Windows 先使用 7-Zip 或其他 gzip 工具将归档解压为 `flight_ads_20260724.sql`，然后在 CMD 或 PowerShell 中执行：

```powershell
cmd /c "mysql -u root -p flight_ads < flight_ads_20260724.sql"
```

Linux 可直接流式导入：

```bash
gzip -dc flight_ads_20260724.sql.gz | mysql -u root -p flight_ads
```

不要使用文本编辑器打开或另存大型 SQL 文件，以免改变编码或截断内容。

## 6. 创建后端只读账号

用管理账号执行以下 SQL，并将占位密码替换为只在本机使用的密码：

```sql
CREATE USER IF NOT EXISTS 'flight_ads_reader'@'127.0.0.1'
  IDENTIFIED BY '<local-password>';
GRANT SELECT ON flight_ads.*
  TO 'flight_ads_reader'@'127.0.0.1';
FLUSH PRIVILEGES;
```

后端使用环境变量或本机私密配置保存连接信息，不要把密码提交到 Git：

```text
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=flight_ads
DB_USER=flight_ads_reader
DB_PASSWORD=<local-password>
```

## 7. 验证恢复结果

```sql
USE flight_ads;

SELECT 'ads_route_lowest_price' AS table_name, COUNT(*) AS row_count
FROM ads_route_lowest_price
UNION ALL
SELECT 'ads_route_cabin_lowest_price', COUNT(*)
FROM ads_route_cabin_lowest_price
UNION ALL
SELECT 'ads_route_offer_rank', COUNT(*)
FROM ads_route_offer_rank
UNION ALL
SELECT 'ads_airline_offer_share', COUNT(*)
FROM ads_airline_offer_share;
```

预期结果：

| 表名 | 行数 |
| --- | ---: |
| `ads_route_lowest_price` | 26,562 |
| `ads_route_cabin_lowest_price` | 714,982 |
| `ads_route_offer_rank` | 1,246 |
| `ads_airline_offer_share` | 71 |

## 8. 航班结果查询口径

- 查询指定出发机场、到达机场和出发日期；
- 页面不提供 `search_date` 时，选择该查询条件下可用的最新采集日；
- 前端未指定舱型时，每个 `departure_time_epoch` 从所有舱型中选择最低价；
- 指定舱型时，先过滤 `cabin_type`，再生成起飞时间列表；
- 按 `departure_time_epoch, lowest_price, quote_snapshot_id` 稳定排序；
- 完成每个起飞时刻的最低价选择后再分页，默认返回 15 条，可请求 10 条；
- `departure_time_raw` 和 `arrival_time_raw` 保留当地时区偏移，不能当作无时区字符串处理。

完整字段和参考 SQL 见项目根目录下的 `docs/ads_data_dictionary.md`。
