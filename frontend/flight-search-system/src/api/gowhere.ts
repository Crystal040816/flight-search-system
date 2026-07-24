import request from '@/utils/request'

export interface DestinationItem {
  city: string
  continent: string
  country: string
  departure: string
  departureCity: string
  destination: string
  lowestPrice: number
}

export interface WhereToGoParams {
  date: string
  departureCity: string
}

export interface WhereToGoResponse {
  code: number
  data: {
    destinations: DestinationItem[]
    total: number
  }
  message: string
}

// “到哪儿去”地图数据接口
export function getWhereToGo(params: WhereToGoParams) {
  return request.post<WhereToGoResponse>('/api/destinations', params)
}
