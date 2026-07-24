import request from '@/utils/request'

export interface SpliceParams {
  date: string
  departure: string
  destination: string
  maxStops?: number
}

export interface Segment {
  aircraftModel: string
  airline: string
  airlineCode: string
  arrivalTime: string
  departureTime: string
  duration: string
  fromAirport: string
  price: number
  toAirport: string
}

export interface SpliceRoute {
  legId: string
  segments: Segment[]
  stops: number
  totalDuration: string
  totalPrice: number
}

// 智能拼接接口
export const getSpliceFlights = (data: SpliceParams) => {
  return request({
    url: '/api/splice',
    method: 'post',
    data
  })
}
