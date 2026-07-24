import axios from 'axios'

// 创建 axios 实例
const request = axios.create({
  baseURL: 'http://192.168.100.136:5000',
  timeout: 10000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => response,
  error => {
    console.error(error)
    return Promise.reject(error)
  }
)

export default request
