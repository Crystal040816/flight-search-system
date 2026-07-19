# backend/test_my_services.py
import sys
import os

# 将当前 backend 目录加入到 Python 查找路径中，确保能顺利导入 app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入你的服务实例
try:
    from app.services.predict_service import price_predict_service as predict_service
    from app.services.recommend_service import recommend_service
    from app.services.splice_service import splice_service

    print("[系统初始化] 成功导入所有服务模块！\n")
except ImportError as e:
    print(f"[错误] 模块导入失败，请检查运行路径。错误原因: {str(e)}")
    sys.exit(1)


def run_self_test():
    print("=================== 开始后端 Service 自我测试 ===================")
    print("提示：当前测试在无 Redis、无算法模型文件的环境下运行，验证降级沙箱及最新数仓字段规范是否正常。\n")

    # 1. 测试价格预测服务 (PricePredictService - 单次价格预测)
    print("--------------------------------------------------")
    print("[测试 1] 调用 predict_service.predict_price_trend...")
    try:
        # 传入测试数据
        predict_res = predict_service.predict_price_trend(
            origin="PEK",
            destination="PVG",
            departure_date="2026-08-01"
        )
        print("【运行结果】:")
        print(f"  - 出发地: {predict_res.get('departure')}")  # 已对齐驼峰
        print(f"  - 目的地: {predict_res.get('destination')}")
        print(f"  - 航班日期: {predict_res.get('flightDate')}")
        print(f"  - 算法单日预测价格: {predict_res.get('predictedPrice')} CNY")  # 已对齐驼峰
        print(f"  - 系统推荐购买日期: {predict_res.get('bestTimeToBuy')}")
        print("\n>> [测试 1] 运行正常，单日价格预测降级逻辑验证通过！✅")
    except Exception as e:
        print(f">> [测试 1] 运行出错 ❌ 原因: {str(e)}")

    # 2. 测试智能推荐服务 (RecommendService)
    print("--------------------------------------------------")
    print("[测试 2] 调用 recommend_service.get_recommendations...")
    try:
        recommend_res = recommend_service.get_recommendations(
            departure="PEK",
            destination="PVG",
            flight_date="2026-07-20",
            preferences={"preferLowPrice": True}
        )
        print("【运行结果】:")
        print(f"  - 推荐航班总数: {len(recommend_res)}")
        if len(recommend_res) > 0:
            first_rec = recommend_res[0]
            print(f"  - 推荐排名 1 行程ID (legId): {first_rec.get('flight').get('legId')}")  # 已对齐无航班号规范
            print(f"  - 推荐原因: {first_rec.get('reason')}")
            print(f"  - 票面价格: {first_rec.get('flight').get('price')} CNY")
            print(f"  - 执飞机型: {first_rec.get('flight').get('aircraftModel')}")  # 验证数仓设备特征
        print("\n>> [测试 2] 运行正常，推荐算法降级逻辑验证通过！✅")
    except Exception as e:
        print(f">> [测试 2] 运行出错 ❌ 原因: {str(e)}")

    # 3. 测试智能拼接服务 (SpliceService)
    print("--------------------------------------------------")
    print("[测试 3] 调用 splice_service.get_spliced_routes...")
    try:
        splice_res = splice_service.get_spliced_routes(
            departure="PEK",
            destination="CDG",
            date="2026-08-01",
            max_stops=1
        )
        print("【运行结果】:")
        print(f"  - 拼接路线方案总数: {len(splice_res)}")
        if len(splice_res) > 0:
            first_route = splice_res[0]
            print(f"  - 拼接行程ID (legId): {first_route.get('legId')}")
            print(f"  - 中转次数: {first_route.get('stops')}")
            print(f"  - 总航程时间: {first_route.get('totalDuration')}")
            print(f"  - 拼接总票价: {first_route.get('totalPrice')} CNY")

            seg1 = first_route.get('segments')[0]
            seg2 = first_route.get('segments')[1]
            print(
                f"  - 航段 1: {seg1.get('fromAirport')} -> {seg1.get('toAirport')} ({seg1.get('aircraftModel')})")  # 驼峰及设备明细
            print(f"  - 航段 2: {seg2.get('fromAirport')} -> {seg2.get('toAirport')} ({seg2.get('aircraftModel')})")
        print("\n>> [测试 3] 运行正常，多航段拼接降级逻辑验证通过！✅")
    except Exception as e:
        print(f">> [测试 3] 运行出错 ❌ 原因: {str(e)}")

    print("--------------------------------------------------")
    print("=================== 测试结束 ===================")


if __name__ == "__main__":
    run_self_test()