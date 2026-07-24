import request from '@/utils/request'

interface DatesResponse {
  code: number
  data: string[]
  message: string
}

export function getAvailableDates() {
  return request.get<DatesResponse>('/api/search/dates')
}
