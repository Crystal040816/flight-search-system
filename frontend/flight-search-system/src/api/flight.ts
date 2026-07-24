import request from '@/utils/request'

// 1. 定义请求参数接口
export interface FlightSearchFilters {
  airlines?: string[]
}

export interface FlightSearchParams {
  departure: string
  destination: string
  flightDate: string
  searchDate: string
  cabinCode: string
  page: number
  size: number
  sortBy: string
  filters: FlightSearchFilters
}

export interface FlightItem {
  aircraftModel?: string
  airline?: string
  airlineAvgPrice?: number
  airlineCode?: string
  avgPrice: number
  cabin?: string
  cabinSummary?: string
  departure: string
  departureCity?: string
  departureCountryCode?: string
  departureCountryName?: string
  departureTime?: string
  destination: string
  destinationCity?: string
  destinationCountryCode?: string
  destinationCountryName?: string
  distinctLegCount?: number
  duration?: string
  isMixedCabin?: boolean
  legId: string
  lowestPrice: number
  offerSharePct?: number
  previousDayAvgPrice?: number
  priceChangePct?: number
  routeQuoteCount?: number
  routeRank?: number
  seatsRemaining?: number
  stops?: number
}

export interface FlightSearchData {
  flights: FlightItem[]
  total: number
}

interface FlightSearchResponse {
  code: number
  data: FlightSearchData
  message: string
}

// 3. 导出真实的航班搜索请求方法
export function searchFlights(data: FlightSearchParams) {
  return request.post<FlightSearchResponse>('/api/search', data)
}
