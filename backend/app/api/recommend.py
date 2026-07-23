# backend/app/api/recommend.py
from flask import Blueprint, request
from app.models.response import UnifiedResponse
from app.services.recommend_service import recommend_service

recommend_bp = Blueprint('recommend', __name__, url_prefix='/api')


@recommend_bp.route('/recommend', methods=['POST'])
def recommend():
    """
       智能推荐接口 (已对接算法 weights 物理配置)
       ---
       tags:
         - 推荐
       summary: 基于多因素推荐最佳航班
       description: "考虑价格、中转、机型、航司服务，加载物理 recommend_model.pkl 的权重对候选航班进行 Min-Max 归一化综合评分。"
       parameters:
         - name: body
           in: body
           required: true
           schema:
             type: object
             required:
               - departure
               - destination
               - flightDate
             properties:
               departure:
                 type: string
                 description: "出发地 IATA 三字码"
                 example: "LGA"
               destination:
                 type: string
                 description: "目的地 IATA 三字码"
                 example: "SFO"
               flightDate:
                 type: string
                 format: date
                 description: "起飞日期 (2022-04-20 至 2022-06-21)"
                 example: "2022-06-08"
               preferences:
                 type: object
                 properties:
                   preferLowPrice:
                     type: boolean
                     description: "是否偏好低价"
                     example: true
                   preferShortDuration:
                     type: boolean
                     description: "是否偏好短时长"
                     example: false
                   preferDirect:
                     type: boolean
                     description: "是否偏好直飞"
                     example: true
       responses:
         200:
           description: "成功返回推荐排行列表"
           schema:
             type: object
             properties:
               code:
                 type: integer
                 example: 200
               data:
                 type: object
                 properties:
                   total:
                     type: integer
                     example: 1
                   recommendations:
                     type: array
                     items:
                       type: object
                       properties:
                         rank:
                           type: integer
                           example: 1
                         reason:
                           type: string
                           example: "综合性价比打分高达 0.8543，全网第 1 推荐"
                         flight:
                           type: object
                           properties:
                             legId:
                               type: string
                               example: "7a3ff1abd3aef9a..."
                             price:
                               type: number
                               example: 166.61
                             airline:
                               type: string
                               example: "American Airlines"
                             airlineCode:
                               type: string
                               example: "AA"
                             totalScore:
                               type: number
                               description: "算法多维度综合推荐得分"
                               example: 0.8543
       """
    try:
        data = request.get_json()
        if not data:
            return UnifiedResponse.bad_request("请求体不能为空")

        required = ['departure', 'destination', 'flightDate']
        for field in required:
            if field not in data:
                return UnifiedResponse.bad_request(f"缺少必填参数: {field}")

        departure = data.get('departure')
        destination = data.get('destination')
        flight_date = data.get('flightDate')
        preferences = data.get('preferences', {})

        # 调用服务层
        recommendations = recommend_service.get_recommendations(
            departure, destination, flight_date, preferences
        )

        return UnifiedResponse.success({
            "recommendations": recommendations,
            "total": len(recommendations)
        })

    except Exception as e:
        return UnifiedResponse.error(f"服务器错误: {str(e)}")