import request from '@/utils/request'

export interface RecommendParams {
  departure: string
  destination: string
  flightDate: string
  preferences?: {
    preferDirect?: boolean
    preferLowPrice?: boolean
    preferShortDuration?: boolean
  }
}

export interface RecommendFlight {
  aircraftModel: string
  airline: string
  airlineCode: string
  departure: string
  departureCity: string
  destination: string
  destinationCity: string
  departureTime: string
  lowestPrice: number
  avgPrice: number
  stops: number
  totalScore: number
  legId: string
  cabinSummary: string
  duration: string
}

export interface RecommendItem {
  rank: number
  reason: string
  flight: RecommendFlight
}

export const getRecommendFlights = (data: RecommendParams) => {
  return request({
    url: '/api/recommend',
    method: 'post',
    data
  })
}
