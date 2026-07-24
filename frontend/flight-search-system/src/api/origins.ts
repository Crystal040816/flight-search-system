import request from '@/utils/request'

interface OriginsResponse {
  code: number
  data: string[]
  message: string
}

export function getOriginCities() {
  return request.get<OriginsResponse>('/api/search/cities/origins')
}
