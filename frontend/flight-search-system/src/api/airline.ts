import request from '@/utils/request'

export interface Airline {
  code: string
  name: string
}

interface AirlineResponse {
  code: number
  data: Airline[]
}

export function getAirlines() {
  return request.get<AirlineResponse>('/api/airlines')
}
