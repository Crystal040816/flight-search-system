import request from '@/utils/request'

// 1. 请求参数接口（对应实际 Post Payload）
export interface PredictParams {
  days: number           // 预测天数/窗口范围，如 7
  departure: string      // 出发地，如 "LGA"
  destination: string    // 目的地，如 "SFO"
  flightDate: string     // 航班日期，如 "2022-06-08"
}

// 2. 最佳购买推荐类型
export interface BestBuy {
  date: string           // 最佳购买日期，如 "2022-04-23"
  daysToDeparture: number// 距离起飞天数
  price: number          // 预测最低价格
}

// 3. 统计信息类型
export interface Statistics {
  avgPrice: number       // 平均价格
  maxPrice: number       // 最高价格
  minPrice: number       // 最低价格
  totalDays: number      // 总预测天数
}

// 4. 趋势数据单项接口
export interface TrendItem {
  date: string            // 预测日期
  daysToDeparture: number // 距离起飞天数
  predictedPrice: number  // 预测价格（驼峰命名）
}

// 5. 响应体 Data 内部结构
export interface PredictData {
  departure: string       // 出发地
  destination: string     // 目的地
  startDate: string       // 航班日期
  totalDays: number       // 预测天数
  suggestion: string      // 购买建议文本
  bestBuy: BestBuy        // 最佳购买推荐
  statistics: Statistics  // 统计指标
  trend: TrendItem[]      // 趋势数组
}

// 6. 统一 API 响应体结构
export interface PredictResponse {
  code: number
  data: PredictData
  message: string
}

// 7. 导出预测 API 请求函数
export function postApiPredict(params: PredictParams) {
  return request.post<PredictResponse>('/api/predict', params)
}
