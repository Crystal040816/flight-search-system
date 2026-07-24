import request from '@/utils/request'

// 1. 请求参数接口
export interface PredictParams {
  days: number
  departure: string
  destination: string
  flightDate: string
}

// 2. 最佳购买推荐类型
export interface BestBuy {
  date: string
  daysToDeparture: number
  price: number
}

// 3. 统计信息类型
export interface Statistics {
  avgPrice: number
  maxPrice: number
  minPrice: number
  totalDays: number
}

// 4. 趋势数据单项接口
export interface TrendItem {
  date: string
  daysToDeparture: number
  predictedPrice: number
}

// 5. 响应体 Data 内部结构
export interface PredictData {
  departure: string
  destination: string
  startDate: string
  totalDays: number
  suggestion: string
  bestBuy: BestBuy
  statistics: Statistics
  trend: TrendItem[]
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
