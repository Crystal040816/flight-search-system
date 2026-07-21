import os
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from pyspark.sql import SparkSession
import pyspark.sql.functions as F


class PricePredictor:
    """
    集群版机票价格预测模型
    基于最新数据字典修正：直接使用 Hive 表中的 days_to_departure 和 route_id
    """

    def __init__(self):
        self.model = XGBRegressor()
        self.feature_cols = []
        self.label_col = "total_fare"
        self.spark = self._init_spark()

    def _init_spark(self, app_name="FlightPricePredictor"):
        """初始化Spark会话"""
        spark = SparkSession.builder \
            .appName(app_name) \
            .enableHiveSupport() \
            .config("spark.sql.parquet.compression.codec", "snappy") \
            .getOrCreate()
        # 切换到业务数据库 (根据你的实际库名修改)
        spark.sql("USE flight_db")
        return spark

    def load_from_hive(self, start_date="2022-04-18", end_date="2022-04-27"):
        """从Hive dwd_flight_itinerary表读取数据"""
        df = (self.spark.table("dwd_flight_itinerary")
              .where(F.col("search_date").between(start_date, end_date))
              .where(F.col("total_fare") > 0)
              .limit(1000000)
              .toPandas())

        # 类型转换
        df["total_fare"] = df["total_fare"].astype(float)
        # total_distance_miles 允许为空，先转为 float 以便后续处理 NaN
        df["total_distance_miles"] = pd.to_numeric(df["total_distance_miles"], errors='coerce')

        # 确保日期列是 datetime 类型
        df["search_date"] = pd.to_datetime(df["search_date"])
        df["flight_date"] = pd.to_datetime(df["flight_date"])

        print(f"[数据加载] 从Hive读取完成，共 {len(df)} 行样本")
        return df

    def build_features(self, df):
        """特征工程：基于数据字典对齐 + 注入地理位置价格先验(Target Encoding)"""
        df = df.copy()

        # 1. 时间衍生特征
        df["departure_weekday"] = df["flight_date"].dt.dayofweek
        df["departure_month"] = df["flight_date"].dt.month
        df["search_weekday"] = df["search_date"].dt.dayofweek

        # 2. 缺失值处理：total_distance_miles (字典允许缺失)
        df["distance_is_null"] = df["total_distance_miles"].isnull().astype(int)
        if "route_id" in df.columns:
            route_avg_dist = df.groupby("route_id")["total_distance_miles"].transform("mean")
            df["total_distance_miles"] = df["total_distance_miles"].fillna(route_avg_dist)
        df["total_distance_miles"] = df["total_distance_miles"].fillna(df["total_distance_miles"].mean())

        # 3. 布尔型特征转数值 (字典显示是 bool)
        bool_cols = ["is_basic_economy", "is_refundable", "is_non_stop"]
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(int)

        # 4. 高基类别特征频次编码 (辅助特征)
        cat_cols = ["first_airline_code", "market_origin", "market_destination", "route_id"]
        for col in cat_cols:
            if col in df.columns:
                freq_map = df[col].value_counts().to_dict()
                df[f"{col}_freq"] = df[col].map(freq_map)

        # 5. 【核心新增】Target Encoding：注入地理位置/航线的价格先验知识
        global_avg_price = df["total_fare"].mean()

        # 出发地平均价格
        if "market_origin" in df.columns:
            origin_mean = df.groupby("market_origin")["total_fare"].mean()
            df["origin_avg_price"] = df["market_origin"].map(origin_mean).fillna(global_avg_price)

        # 目的地平均价格
        if "market_destination" in df.columns:
            dest_mean = df.groupby("market_destination")["total_fare"].mean()
            df["dest_avg_price"] = df["market_destination"].map(dest_mean).fillna(global_avg_price)

        # 航线平均价格 (最强特征)
        if "route_id" in df.columns:
            route_mean = df.groupby("route_id")["total_fare"].mean()
            df["route_avg_price"] = df["route_id"].map(route_mean).fillna(global_avg_price)

        # 6. 定义最终入模特征列 (严格对齐数据字典)
        self.feature_cols = [
            # 时间/距离类 (字典字段)
            "days_to_departure",
            "travel_duration_minutes",
            "elapsed_days",
            "total_distance_miles",
            "distance_is_null",

            # 布尔/计数类 (字典字段)
            "is_basic_economy",
            "is_refundable",
            "is_non_stop",
            "seats_remaining",
            "segment_count",
            "stop_count",

            # 时间衍生
            "departure_weekday",
            "departure_month",
            "search_weekday",

            # 频次编码特征
            "first_airline_code_freq",
            "market_origin_freq",
            "market_destination_freq",
            "route_id_freq",

            # Target Encoding 特征 (核心)
            "origin_avg_price",
            "dest_avg_price",
            "route_avg_price"
        ]

        # 过滤掉不存在的列
        existing_cols = [c for c in self.feature_cols if c in df.columns]
        self.feature_cols = existing_cols

        # 删除包含空特征的行
        df = df.dropna(subset=self.feature_cols).reset_index(drop=True)

        print(f"[特征工程] 完成，有效样本 {len(df)} 行，入模特征 {len(self.feature_cols)} 个")
        return df

    def generate_lookup_table(self, df, save_path="route_lookup_table.csv"):
        """
        生成用于预测的查找表 (CSV)
        将航线、出发地、目的地的统计信息合并到一个文件中，方便预测时查询
        """
        print("🏗️ 正在生成路线特征查找表...")

        # 1. 航线维度统计 (Route Level) - 以 Origin + Dest 为 Key
        route_stats = df.groupby(["market_origin", "market_destination"]).agg({
            "total_fare": "mean",
            "total_distance_miles": "mean",
            "travel_duration_minutes": "mean",
            "seats_remaining": "median",
            "is_non_stop": "mean",
            "segment_count": "mean",
            "stop_count": "mean"
        }).reset_index()

        route_stats.rename(columns={
            "total_fare": "route_avg_price",
            "total_distance_miles": "route_avg_dist",
            "travel_duration_minutes": "route_avg_duration",
            "seats_remaining": "route_median_seats",
            "is_non_stop": "route_non_stop_prob",
            "segment_count": "route_avg_segments",
            "stop_count": "route_avg_stops"
        }, inplace=True)

        # 2. 出发地维度统计 (Origin Level)
        origin_stats = df.groupby("market_origin")["total_fare"].mean().reset_index()
        origin_stats.rename(columns={"total_fare": "origin_avg_price"}, inplace=True)

        # 3. 目的地维度统计 (Dest Level)
        dest_stats = df.groupby("market_destination")["total_fare"].mean().reset_index()
        dest_stats.rename(columns={"total_fare": "dest_avg_price"}, inplace=True)

        # 4. 合并所有统计信息到一个表
        # 以航线表为基础，左连接出发地和目的地均价
        final_lookup = route_stats.merge(origin_stats, on="market_origin", how="left") \
            .merge(dest_stats, on="market_destination", how="left")

        # 填充可能的 NaN (例如新航线没有历史数据，用全局均价兜底)
        global_avg = df["total_fare"].mean()
        final_lookup["route_avg_price"] = final_lookup["route_avg_price"].fillna(global_avg)
        final_lookup["origin_avg_price"] = final_lookup["origin_avg_price"].fillna(global_avg)
        final_lookup["dest_avg_price"] = final_lookup["dest_avg_price"].fillna(global_avg)

        # 保存
        final_lookup.to_csv(save_path, index=False)
        print(f"✅ 查找表已生成: {save_path} (共 {len(final_lookup)} 条航线)")
        return final_lookup

    def train(self, df):
        """训练XGBoost回归模型"""
        if not self.feature_cols:
            df = self.build_features(df)

        # 按时间顺序划分 (避免时间穿越)
        df = df.sort_values("search_date").reset_index(drop=True)
        split_idx = int(len(df) * 0.8)
        train_mask = df.index < split_idx

        X_train = df.loc[train_mask, self.feature_cols]
        y_train = df.loc[train_mask, self.label_col]
        X_val = df.loc[~train_mask, self.feature_cols]
        y_val = df.loc[~train_mask, self.label_col]

        # 模型训练
        self.model = XGBRegressor(
            n_estimators=300,
            max_depth=7,
            learning_rate=0.08,
            objective="reg:squarederror",
            random_state=42,
            early_stopping_rounds=30
        )
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=50
        )

        # 评估
        y_pred = self.model.predict(X_val)
        y_val_float = y_val.astype(float).values

        mae = mean_absolute_error(y_val_float, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val_float, y_pred))
        epsilon = 1e-5
        mape = np.mean(np.abs(y_val_float - y_pred) / (y_val_float + epsilon)) * 100

        print("=" * 60)
        print(f"[训练完成] 验证集 MAE:  {mae:.2f} USD")
        print(f"[训练完成] 验证集 RMSE: {rmse:.2f} USD")
        print(f"[训练完成] 验证集 MAPE: {mape:.2f} %")
        print("=" * 60)
        return {"mae": mae, "rmse": rmse, "mape": mape}

    def save_model(self, save_path="../models/price_predictor.pkl"):
        """保存模型"""
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        joblib.dump({
            "model": self.model,
            "feature_cols": self.feature_cols
        }, save_path)
        print(f"[模型保存] 已保存到: {os.path.abspath(save_path)}")

    def stop(self):
        self.spark.stop()


if __name__ == "__main__":
    print("=" * 60)
    print("=== 集群版机票价格预测模型 - 全流程训练 ===")
    print("=" * 60)

    predictor = PricePredictor()
    try:
        # 1. 加载数据
        print("\n>>> 步骤1：加载Hive数据")
        raw_df = predictor.load_from_hive("2022-04-18", "2022-04-27")

        # 2. 特征工程
        print("\n>>> 步骤2：执行特征工程")
        feature_df = predictor.build_features(raw_df)

        # 3. 训练
        print("\n>>> 步骤3：训练价格预测模型")
        predictor.train(feature_df)

        # 4. 保存模型
        print("\n>>> 步骤4：保存模型文件")
        predictor.save_model()

        # 5. 生成查找表 (CSV) - 新增步骤
        print("\n>>> 步骤5：生成预测用查找表 (CSV)")
        predictor.generate_lookup_table(raw_df, save_path="route_lookup_table.csv")

        print("\n✅ 全流程执行成功！")
    except Exception as e:
        print(f"\n❌ 执行失败：{str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        predictor.stop()
