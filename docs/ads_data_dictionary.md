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
| `ads_route_cabin_lowest_price` | 搜索日 + 市场航线 + 出发日 + 首段起飞时刻 + 舱型类别 | `search_date, market_origin, market_destination, flight_date, departure_time_epoch, cabin_type` | 714,982 |
| `ads_route_offer_rank` | 搜索日 + 市场航线 | `search_date, route_id` | 1,246 |
| `ads_airline_offer_share` | 搜索日 + 第一航段航司 | `search_date, airline_code` | 71 |

以上为 2026-07-23 发布并通过 MySQL 实表质量检查的正式结果。舱型最低价表的行数增加来自起飞时间粒度，不表示新增了原始报价。

## 3. `ads_route_lowest_price`

| 字段 | MySQL 类型 | 含义 |
| --- | --- | --- |
| `search_date` | DATE | 搜索日期 |
| `market_origin` | VARCHAR(8) | 市场起点机场代码 |
| `origin_city` | VARCHAR(128) | 起点城市，可为空 |
| `origin_country_code` | CHAR(2) | 起点国家代码，可为空 |
| `origin_country_name` | VARCHAR(128) | 起点国家名称，可为空 |
| `market_destination` | VARCHAR(8) | 市场终点机场代码 |
| `destination_city` | VARCHAR(128) | 目的地城市，可为空 |
| `destination_country_code` | CHAR(2) | 目的地国家代码，可为空 |
| `destination_country_name` | VARCHAR(128) | 目的地国家名称，可为空 |
| `flight_date` | DATE | 出发日期 |
| `departure_time_raw` | VARCHAR(64) | 最低价行程首航段的原始起飞时间，保留源时区偏移 |
| `departure_time_epoch` | BIGINT | 最低价行程首航段起飞 Epoch 秒，用于排序和计算 |
| `arrival_time_raw` | VARCHAR(64) | 最低价行程末航段的原始到达时间，保留源时区偏移 |
| `arrival_time_epoch` | BIGINT | 最低价行程末航段到达 Epoch 秒 |
| `travel_duration_minutes` | INT | 整条行程总时长（分钟），包含中转等待 |
| `lowest_price` | DECIMAL(12,2) | 该粒度下最低含税报价 |
| `avg_price` | DECIMAL(12,2) | 该粒度下平均含税报价 |
| `quote_snapshot_id` | CHAR(64) | 最低价对应的 DWD 报价快照 |
| `airline_code` | VARCHAR(8) | 最低价报价的第一航段航司代码 |
| `airline_name` | VARCHAR(128) | 最低价报价的第一航段航司名称 |
| `seats_remaining` | INT | 最低价行程报价的剩余座位，可为空 |
| `cabin_type` | VARCHAR(32) | 单一舱型代码；跨航段舱型不同时为 `mixed`，缺失时为 `unknown` |
| `cabin_summary` | VARCHAR(255) | 按航段顺序排列的舱型代码，以 `||` 分隔 |
| `is_mixed_cabin` | BOOLEAN | 是否包含多个不同舱型 |
| `equipment_summary` | VARCHAR(1024) | 按航段顺序排列的机型描述，以 `||` 分隔；缺失航段为 `unknown` |
| `currency` | CHAR(3) | 币种，当前为 USD |
| `etl_time` | DATETIME(6) | ETL 处理时间 |

索引支持按搜索日、目的地和最低价筛选，以及按 `flight_date` 查询。

该表保留样本中的绝对最低报价，可能出现 `seats_remaining=0`。此时前端应标记“无余票”，不能把该价格称为“最低可购买价”。`airline_name` 和 `airline_code` 仅表示第一航段航司。

## 4. `ads_route_cabin_lowest_price`

该表用于同一航线、同一出发日和同一首段起飞时刻下按舱型比较整条行程报价。`lowest_price` 和 `avg_price` 都是行程含税总价，不是单航段票价。前端可以不提供舱型选项：未指定舱型时，后端在每个起飞时间中从所有舱型选择价格最低的一行；将来增加舱型筛选时，后端先按指定 `cabin_type` 过滤，再按起飞时间返回列表。ADS 保留舱型字段和粒度，以支持该扩展，不要求当前前端必须展示舱型控件。

| 字段 | MySQL 类型 | 含义 |
| --- | --- | --- |
| `search_date` | DATE | 搜索日期 |
| `market_origin` | VARCHAR(8) | 市场起点机场代码 |
| `origin_city` | VARCHAR(128) | 起点城市，可为空 |
| `origin_country_code` | CHAR(2) | 起点国家代码，可为空 |
| `origin_country_name` | VARCHAR(128) | 起点国家名称，可为空 |
| `market_destination` | VARCHAR(8) | 市场终点机场代码 |
| `destination_city` | VARCHAR(128) | 目的地城市，可为空 |
| `destination_country_code` | CHAR(2) | 目的地国家代码，可为空 |
| `destination_country_name` | VARCHAR(128) | 目的地国家名称，可为空 |
| `flight_date` | DATE | 出发日期 |
| `departure_time_raw` | VARCHAR(64) | 该舱型最低价行程首航段的原始起飞时间 |
| `departure_time_epoch` | BIGINT | 该舱型最低价行程首航段起飞 Epoch 秒，也是主键的一部分 |
| `arrival_time_raw` | VARCHAR(64) | 该舱型最低价行程末航段的原始到达时间 |
| `arrival_time_epoch` | BIGINT | 该舱型最低价行程末航段到达 Epoch 秒 |
| `travel_duration_minutes` | INT | 整条行程总时长（分钟），包含中转等待 |
| `cabin_type` | VARCHAR(32) | 比较分组：单一舱型、`mixed` 或 `unknown` |
| `cabin_summary` | VARCHAR(255) | 最低价行程的逐航段舱型序列 |
| `is_mixed_cabin` | BOOLEAN | 最低价行程是否为混合舱型 |
| `lowest_price` | DECIMAL(12,2) | 该起飞时刻和舱型下最低行程含税总价 |
| `avg_price` | DECIMAL(12,2) | 该起飞时刻和舱型下平均行程含税总价 |
| `offer_count` | BIGINT | 该起飞时刻和舱型分组包含的报价快照数 |
| `quote_snapshot_id` | CHAR(64) | 最低价对应的 DWD 报价快照 |
| `airline_code` | VARCHAR(8) | 最低价行程第一航段航司代码 |
| `airline_name` | VARCHAR(128) | 最低价行程第一航段航司名称 |
| `seats_remaining` | INT | 最低价行程报价的剩余座位，可为空 |
| `equipment_summary` | VARCHAR(1024) | 最低价行程的逐航段机型序列 |
| `currency` | CHAR(3) | 币种，当前为 USD |
| `etl_time` | DATETIME(6) | ETL 处理时间 |

舱型来自 DWD 航段记录。所有已知航段舱型相同时，`cabin_type` 使用该代码；出现两个或以上不同舱型时归为 `mixed`；全部缺失时归为 `unknown`。

## 5. `ads_route_offer_rank`

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

## 6. `ads_airline_offer_share`

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

## 7. 只读查询示例

以下示例不包含账号和密码：

```sql
SELECT
    search_date,
    market_origin,
    origin_city,
    market_destination,
    destination_city,
    flight_date,
    departure_time_raw,
    arrival_time_raw,
    travel_duration_minutes,
    lowest_price,
    airline_code,
    cabin_type,
    seats_remaining,
    equipment_summary
FROM flight_ads.ads_route_lowest_price
WHERE search_date = '2022-04-19'
ORDER BY lowest_price
LIMIT 20;
```

按舱型比较最低行程报价：

```sql
SELECT
    search_date,
    market_origin,
    origin_city,
    market_destination,
    destination_city,
    flight_date,
    departure_time_raw,
    arrival_time_raw,
    travel_duration_minutes,
    cabin_type,
    lowest_price,
    avg_price,
    offer_count,
    seats_remaining
FROM flight_ads.ads_route_cabin_lowest_price
WHERE search_date = '2022-04-19'
  AND market_origin = 'ATL'
  AND market_destination = 'LAX'
ORDER BY flight_date, departure_time_epoch, cabin_type, lowest_price;
```

查询指定航线与出发日的最新采集批次，并按起飞时间展示最低价：

```sql
WITH ranked AS (
    SELECT
        cabin_price.*,
        ROW_NUMBER() OVER (
            PARTITION BY
                search_date,
                market_origin,
                market_destination,
                flight_date,
                departure_time_epoch
            ORDER BY
                lowest_price,
                travel_duration_minutes,
                quote_snapshot_id
        ) AS time_price_rank
    FROM flight_ads.ads_route_cabin_lowest_price AS cabin_price
    WHERE market_origin = 'ATL'
      AND market_destination = 'LAX'
      AND flight_date = '2022-05-10'
      AND search_date = (
          SELECT MAX(search_date)
          FROM flight_ads.ads_route_cabin_lowest_price
          WHERE market_origin = 'ATL'
            AND market_destination = 'LAX'
            AND flight_date = '2022-05-10'
      )
)
SELECT
    search_date,
    market_origin,
    origin_city,
    market_destination,
    destination_city,
    flight_date,
    departure_time_raw,
    arrival_time_raw,
    travel_duration_minutes,
    lowest_price,
    airline_name,
    cabin_type,
    seats_remaining
FROM ranked
WHERE time_price_rank = 1
ORDER BY departure_time_epoch, lowest_price, quote_snapshot_id
LIMIT 15 OFFSET 0;
```

上例是不指定舱型时的默认查询：窗口函数先为每个起飞时刻选择所有舱型中的最低价，再排序和分页。若前端传入舱型，应该在 `ranked` CTE 内增加参数化条件 `AND cabin_price.cabin_type = ?`；不能在窗口函数完成后才筛选舱型，否则该时刻目标舱型可能已经被其他舱型淘汰。

后端建议把 `page_size` 默认值固定为 15，并允许前端显式传入 10；为了避免一次返回过多数据，可将最大值限制为 50。`LIMIT` 必须位于 `time_price_rank = 1` 之后，并使用 `departure_time_epoch, lowest_price, quote_snapshot_id` 作为稳定排序。若需要下一页，可使用 `LIMIT ? OFFSET ?`；数据量继续增大时再改为基于 `departure_time_epoch` 和 `quote_snapshot_id` 的游标分页。

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

## 8. Windows 通过 SSH 隧道访问

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
| Password | 通过安全渠道单独提供 |

这里必须连接本地端口 `13306`，不能把客户端端口填写成远端 MySQL 的 `3306`。使用结束后，在 SSH 隧道窗口按 `Ctrl+C` 即可关闭转发。

如果组员电脑无法访问 `192.168.100.27:22`，说明该电脑不在虚拟机网络可达范围内。此时应使用同一宿主机、VPN 或另行配置受控的 SSH 入口，不要直接开放 MySQL 端口。

保持 SSH 隧道窗口开启，新建 MySQL 连接：
Host:     127.0.0.1
Port:     13306
Database: flight_ads
Username: flight_ads_reader
Password: 由成员提供

连接成功后执行：
SELECT
    DATABASE() AS database_name,
    CURRENT_USER() AS authenticated_account,
    @@hostname AS mysql_host,
    @@port AS mysql_port;

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

预期账号为 `flight_ads_reader@127.0.0.1`，四张表行数应为 26,562、714,982、1,246 和 71。

2026-07-23 业务抽查选择 `search_date=2022-04-19`、`LAX` 到 `BOS`、`flight_date=2022-04-26`，按每个 `departure_time_epoch` 选最低价后返回 67 行，包含 67 个不同起飞时刻，重复数为 0。

## 9. 接口和展示约束

- API 和图表必须允许用户选择 `search_date`，不能默认把 6 个不连续日期当作连续时间序列；
- 航班结果页若不暴露 `search_date`，后端应选择指定航线与 `flight_date` 可用的最新采集日，不能混合多个采集批次；
- 前端可以不提供舱型选项；未指定舱型时，多时间结果读取 `ads_route_cabin_lowest_price`，按 `departure_time_epoch` 为每个时刻选择所有舱型中的最低价；指定舱型时必须先过滤 `cabin_type`，再生成起飞时间列表；
- 更新后记录数量大一个数量级（27000+~7000000+）如果当日航班数量过多，请前后端自行商讨结果页中展示的数量；必须先完成舱型过滤或每时刻最低价选择，再按 `departure_time_epoch, lowest_price, quote_snapshot_id` 稳定排序，最后执行 `LIMIT/OFFSET`；
- 金额字段显示 USD，并保留两位小数；
- `price_change_pct` 已是百分比数值，展示前确认组件是否还会乘以 100；
- 目的地城市和国家字段允许为空，前端需要提供回退显示；
- 起点城市和国家字段也允许为空，回退显示对应 IATA 代码；
- `cabin_type=mixed` 表示中转行程包含不同舱型，不能展示成单一舱型；
- 舱型价格是整条行程总价，不是单航段价格；
- `departure_time_raw` 是首航段当地起飞时间，`arrival_time_raw` 是末航段当地到达时间；前端不应丢弃字符串中的时区偏移；
- `travel_duration_minutes` 是整条行程耗时并包含中转等待，不等于各航段纯飞行时间之和；
- 时间排序和耗时校验优先使用 epoch 字段，不要直接按带时区字符串排序；
- `equipment_summary` 中的 `unknown` 表示原始数据没有该航段机型；
- 原始数据没有航班号和航站楼，接口不得使用 `leg_id` 等字段伪造；
- `seats_remaining=0` 表示样本报价无余票，不应展示为当前可购买；
- `airline_name` 是首段航司，中转行程不能描述为全程唯一承运航司；
- 不要向浏览器、代码仓库或共享文档写入 MySQL 密码；
- ADS 更新后，应同时检查 Hive 基线质量记录和 `data_engineering/mysql/ads_quality_checks.sql` 的 MySQL 实表结果；不能用旧 Hive `run_id` 代替新发布验收。
