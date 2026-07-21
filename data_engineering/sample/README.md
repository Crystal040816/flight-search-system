# DWD 算法样本交付说明

## 交付内容

| 文件 | 用途 |
| --- | --- |
| `dwd_sample.parquet` | 5 万行算法开发样本，Parquet/Snappy 格式 |
| `dwd_ddl.sql` | 完整 DWD Hive 表结构与字段注释 |
| `data_dictionary.csv` | 当前样本 18 个字段的数据字典与建模角色 |
| `schema.json` | 从 Parquet 文件读取的机器可读 Schema |
| `profile.json` | 样本质量、日期范围、覆盖率和数值统计 |
| `sample_metadata.json` | 数据来源、抽样方法和适用范围 |
| `read_sample.py` | Pandas/PyArrow 读取和基础校验示例 |
| `requirements.txt` | 读取样本所需的最小 Python 依赖 |
| `SHA256SUMS.txt` | 交付文件完整性校验值 |

## 数据范围

- 原始行程数据：82,138,753 行。
- DWD 实验数据：1,000,000 行，采用 `FIRST_N_ROWS` 非均衡样本。
- 本地算法样本：从 DWD 实验数据中 `LIMIT 50000` 导出。
- 本地样本行数：50,000。
- 搜索日期：仅 `2022-04-19`。
- 出发日期：`2022-04-20` 至 `2022-04-25`，共 6 天。
- 航线：234 条。
- 首段航司代码：12 个。

该样本适合字段联调、特征工程、票价预测基线和接口开发。由于只包含一个搜索日期，它不适合时间趋势分析、跨日期验证或生产模型精度声明。

## 建模约定

- 推荐预测目标：`total_fare`。
- 标识字段：`quote_snapshot_id`，不可作为模型特征。
- 日期字段：`search_date`、`flight_date`，应派生星期、月份等特征后使用。
- 已派生特征：`days_to_departure`、`route_id`、`segment_count`、`stop_count`。
- 类别特征：`route_id`、`market_origin`、`market_destination`、`first_airline_code`。
- `total_distance_miles` 允许为空；当前空值 2,563 个，占 5.126%。算法需填补、增加缺失标记或使用支持缺失值的模型。
- `total_fare` 是标签时，必须从输入特征中删除，避免目标泄漏。

## 快速开始

建议使用 Python 3.10 或更高版本：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python read_sample.py
```

直接读取：

```python
import pandas as pd

df = pd.read_parquet("dwd_sample.parquet", engine="pyarrow")
print(df.shape)
print(df.head())
```

Parquet 自带字段名和类型；`dwd_ddl.sql` 用于解释字段业务含义及其他 DWD 表关系。

## 质量基线

- `quote_snapshot_id`：无空值、无重复。
- 除 `total_distance_miles` 外，其余 17 列无空值。
- 总价范围：35.98 至 4,752.60 USD。
- 全程时长范围：48 至 1,459 分钟。
- 航段数量范围：1 至 4。
- 搜索提前期范围：1 至 6 天。

运行 `read_sample.py` 会再次检查行数、必要字段、唯一键和日期范围；若交付文件被替换为不兼容版本，脚本会直接失败。
