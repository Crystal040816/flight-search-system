import axios from 'axios'

// 获取出发机场列表接口
export const getOriginAirports = (cityName: string) => {
  return axios.get('http://192.168.100.27:5000/api/search/airports/origins', {
    params: {
      city: cityName // 自动拼接 ?city=xxx
    }
  })
}

// 获取目的地机场接口
export const getDestinationAirports = (cityName: string) => {
  return axios.get('http://192.168.100.27:5000/api/search/airports/destinations', {
    params: { city: cityName }
  })
}
