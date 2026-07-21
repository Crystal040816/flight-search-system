# ADS 数据字典与使用说明

## 1. 层级定位

ADS 是面向后端 API、Superset 和演示页面的服务层。当前正式交付目标为 `node-master` 本机 MySQL 数据库 `flight_ads`，由 Spark 从 Hive DWD/DWS 计算后通过 JDBC 写入。

- MySQL 地址：`127.0.0.1:3306`
- 数据库：`flight_ads`
- 字符集：`utf8mb4`
- 存储引擎：InnoDB
- 写入账号：仅供 ETL 使用，不向下游共享
- 下游账号：应另建只读账号并只授予 `SELECT`

`data_engineering/hive/ads_ddl.sql` 描述逻辑指标结构；当前应用实际读取 `data_engineering/mysql/ads_ddl.sql` 创建的 MySQL 表。

## 2. 表清单

| 表名 | 粒度 | 主键 | 当前行数 |
| --- | --- | --- | ---: |
| `ads_route_lowest_price` | 搜索日 + 市场航线 + 出发日 | `search_date, market_origin, market_destination, flight_date` | 26,562 |
| `ads_route_offer_rank` | 搜索日 + 市场航线 | `search_date, route_id` | 1,246 |
| `ads_airline_offer_share` | 搜索日 + 第一航段航司 | `search_date, airline_code` | 71 |

## 3. `ads_route_lowest_price`

| 字段 | MySQL 类型 | 含义 |
| --- | --- | --- |
| `search_date` | DATE | 搜索日期 |
| `market_origin` | VARCHAR(8) | 市场起点机场代码 |
| `market_destination` | VARCHAR(8) | 市场终点机场代码 |
| `destination_city` | VARCHAR(128) | 目的地城市，可为空 |
| `destination_country_code` | CHAR(2) | 目的地国家代码，可为空 |
| `destination_country_name` | VARCHAR(128) | 目的地国家名称，可为空 |
| `flight_date` | DATE | 出发日期 |
| `lowest_price` | DECIMAL(12,2) | 该粒度下最低含税报价 |
| `avg_price` | DECIMAL(12,2) | 该粒度下平均含税报价 |
| `quote_snapshot_id` | CHAR(64) | 最低价对应的 DWD 报价快照 |
| `airline_code` | VARCHAR(8) | 最低价报价的第一航段航司代码 |
| `airline_name` | VARCHAR(128) | 最低价报价的第一航段航司名称 |
| `currency` | CHAR(3) | 币种，当前为 USD |
| `etl_time` | DATETIME(6) | ETL 处理时间 |

索引支持按搜索日、目的地和最低价筛选，以及按 `flight_date` 查询。

## 4. `ads_route_offer_rank`

| 字段 | MySQL 类型 | 含义 |
| --- | --- | --- |
| `search_date` | DATE | 搜索日期 |
| `rank_num` | INT | 当日按报价数量生成的航线排名 |
| `route_id` | VARCHAR(32) | 市场航线标识 |
| `market_origin` | VARCHAR(8) | 市场起点机场代码 |
| `market_destination` | VARCHAR(8) | 市场终点机场代码 |
| `quote_count` | BIGINT | 当日该航线的报价快照数 |
| `distinct_leg_count` | BIGINT | 当日不同航程标识数 |
| `avg_price` | DECIMAL(12,2) | 当日平均含税报价 |
| `previous_day_avg_price` | DECIMAL(12,2) | 样本中前一个可用搜索日的平均价，可为空 |
| `price_change_pct` | DECIMAL(9,4) | 相对前一个可用搜索日的平均价变化百分比，可为空 |
| `etl_time` | DATETIME(6) | ETL 处理时间 |

同一搜索日的 `rank_num` 唯一。该排名反映报价记录供给量，不代表客流、销量或航线真实热度。

## 5. `ads_airline_offer_share`

| 字段 | MySQL 类型 | 含义 |
| --- | --- | --- |
| `search_date` | DATE | 搜索日期 |
| `airline_code` | VARCHAR(8) | 第一航段航司代码 |
| `airline_name` | VARCHAR(128) | 第一航段航司名称 |
| `quote_count` | BIGINT | 当日归属于该航司的报价数 |
| `offer_share_pct` | DECIMAL(9,6) | 当日报价供给百分比，合计约 100 |
| `avg_price` | DECIMAL(12,2) | 当日该航司平均含税报价 |
| `etl_time` | DATETIME(6) | ETL 处理时间 |

`offer_share_pct` 不是销售市场份额。展示名称应使用“报价供给占比”或“报价覆盖占比”。

## 6. 只读查询示例

以下示例不包含账号和密码：

```sql
SELECT
    search_date,
    market_origin,
    market_destination,
    flight_date,
    lowest_price,
    airline_code
FROM flight_ads.ads_route_lowest_price
WHERE search_date = '2022-04-19'
ORDER BY lowest_price
LIMIT 20;
```

```sql
SELECT
    search_date,
    rank_num,
    route_id,
    quote_count,
    avg_price,
    price_change_pct
FROM flight_ads.ads_route_offer_rank
WHERE search_date = '2022-04-19'
ORDER BY rank_num;
```

```sql
SELECT
    search_date,
    airline_code,
    offer_share_pct,
    avg_price
FROM flight_ads.ads_airline_offer_share
WHERE search_date = '2022-04-19'
ORDER BY offer_share_pct DESC;
```

## 7. Windows 通过 SSH 隧道访问

MySQL 当前只监听 `node-master` 的 `127.0.0.1:3306`，不要为了联调把数据库直接暴露到局域网。Windows 用户先在 PowerShell 中建立 SSH 隧道：

```powershell
ssh -N `
  -L 13306:127.0.0.1:3306 `
  hadoop@192.168.100.27
```

SSH 窗口保持无输出表示隧道正在运行，不要关闭。另开一个 PowerShell 窗口可检查：

```powershell
Test-NetConnection 127.0.0.1 -Port 13306
```

MySQL Workbench、DBeaver、IDE 数据库工具或后端程序统一使用以下连接参数：

| 参数 | 值                   |
| --- |---------------------|
| Host | `127.0.0.1`         |
| Port | `13306`             |
| Database/Schema | `flight_ads`        |
| Username | `flight_ads_reader` |
| Password |              |

这里必须连接本地端口 `13306`，不能把客户端端口填写成远端 MySQL 的 `3306`。使用结束后，在 SSH 隧道窗口按 `Ctrl+C` 即可关闭转发。

如果组员电脑无法访问 `192.168.100.27:22`，说明该电脑不在虚拟机网络可达范围内。此时应使用同一宿主机、VPN 或另行配置受控的 SSH 入口，不要直接开放 MySQL 端口。

## 8. 接口和展示约束

- API 和图表必须允许用户选择 `search_date`，不能默认把 6 个不连续日期当作连续时间序列；
- 金额字段显示 USD，并保留两位小数；
- `price_change_pct` 已是百分比数值，展示前确认组件是否还会乘以 100；
- 目的地城市和国家字段允许为空，前端需要提供回退显示；
- 不要向浏览器、代码仓库或共享文档写入 MySQL 密码；
- ADS 更新后，应检查 Hive `flight_db.dq_check_result` 中对应 ADS 批次全部通过。
