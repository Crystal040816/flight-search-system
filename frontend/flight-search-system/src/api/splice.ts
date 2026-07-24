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

export interface SpliceData {
  routes: SpliceRoute[]
  total: number
}

export interface SpliceResponse {
  code: number
  data: SpliceData
  message: string
}

export const getSpliceFlights = (data: SpliceParams) => {
  return request.post<SpliceResponse>('/api/splice', data)
}
