import request from '@/utils/request'

interface DestinationsResponse {
  code: number
  data: string[]
  message: string
}

export function getDestinationCities() {
  return request.get<DestinationsResponse>('/api/search/cities/destinations')
}
