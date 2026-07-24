<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed} from 'vue'
import {
  Switch, Search, Operation, Refresh,
  SuccessFilled, Promotion, Clock, InfoFilled, TrendCharts
} from '@element-plus/icons-vue'

import { useRoute } from 'vue-router'

const route = useRoute()

// 引入存放图片的相对路径
import skyBg from '../pictures/天空.jpg'

//引入接口
import { getAirlines, type Airline } from '@/api/airline'
import { getOriginCities } from '@/api/origins'
import { getDestinationCities } from '@/api/destinations'
import { getAvailableDates } from '@/api/dates'
import { getOriginAirports, getDestinationAirports } from '@/api/airports'
import { searchFlights, type FlightSearchParams, type FlightItem } from '@/api/flight'
import { getSpliceFlights, type SpliceRoute } from '@/api/splice'

// 分别定义出发和到达城市的选项数据
const originOptions = ref<{ label: string; value: string }[]>([])
const destOptions = ref<{ label: string; value: string }[]>([])

// 顶部搜索表单状态
const passengers = ref('')
const fromCity = ref('') // 对应下拉菜单的初始值
const toCity = ref('')   // 对应下拉菜单的初始值
const departureDate = ref('')
const availableDates = ref<string[]>([])

// 声明出发机场的响应式数据
const departureAirportOptions = ref<string[]>([]) // 存储接口返回的机场代码数组
const selectedAirport = ref('') // 用户选中的具体机场

const destinationAirportOptions = ref<string[]>([]) // 目的地机场选项
const selectedDestAirport = ref('')               // 选中的目的地机场

const selectedAirline = ref('')
const airlineList = ref<Airline[]>([])

const flightList = ref<any[]>([])
const loadingFlights = ref(false)

// 1. 定义当前排序字段（默认：价格 price）
// 可选值：'price' | 'duration' | 'depTime' | 'arrTime'
const sortBy = ref<string>('price')

// 声明模式状态与拼接航班数据列表
const currentMode = ref<'free' | 'package'>('free') // free: 自由搭配, package: 航班组合
const splicedFlightList = ref<SpliceRoute[]>([])

// 航程详情弹窗逻辑与 ADS 数据绑定
const detailVisible = ref(false)
const loadingDetail = ref(false)

// 点击中间的切换图标时，互换出发地和目的地
const swapCities = () => {
  const temp = fromCity.value
  fromCity.value = toCity.value
  toCity.value = temp
  selectedAirport.value = ''
  selectedDestAirport.value = ''
}

// 切换排序方式的方法
const handleSortChange = (type: string) => {
  sortBy.value = type
}

// 舱位映射字典/函数
const formatCabin = (cabin?: string): string => {
  if (!cabin) return '经济舱'
  const c = cabin.toLowerCase()
  if (c === 'coach' ) {
    return '经济舱'
  }
  return cabin
}

// 时间格式化工具函数：兼容单时刻提取与“日期+时间”格式化
const formatTime = (dateTimeStr?: string): string => {
  if (!dateTimeStr) return '--:--'
  if (dateTimeStr.includes(', ')) {
    return dateTimeStr.split(', ')[1].substring(0, 5)
  }
  if (dateTimeStr.includes(' ')) {
    return dateTimeStr.split(' ')[1].substring(0, 5)
  }
  if (dateTimeStr.includes('T')) {
    return dateTimeStr.split('T')[1].substring(0, 5)
  }
  return dateTimeStr.substring(0, 5)
}

// 模板中解析“年月日 + HH:mm”的函数
const formatFlightTime = (dateTimeStr?: string) => {
  if (!dateTimeStr) return { date: '--', time: '--:--' }

  // 1. 提取 HH:mm 时间
  const time = formatTime(dateTimeStr)

  // 2. 提取 YYYY-MM-DD 或 YYYY/MM/DD 部分
  let datePart = ''

  if (dateTimeStr.includes(', ')) {
    datePart = dateTimeStr.split(', ')[0]
  } else if (dateTimeStr.includes('T')) {
    datePart = dateTimeStr.split('T')[0]
  } else if (dateTimeStr.includes(' ')) {
    datePart = dateTimeStr.split(' ')[0]
  } else {
    datePart = dateTimeStr
  }

  // 3. 匹配年-月-日并格式化
  const dateMatch = datePart.match(/(\d{4})[-/](\d{1,2})[-/](\d{1,2})/)
  if (dateMatch) {
    const [, y, m, d] = dateMatch
    // 补齐两位数 (如 04月)
    const formattedM = m.padStart(2, '0')
    const formattedD = d.padStart(2, '0')
    return {
      date: `${y}年${formattedM}月${formattedD}日`,
      time
    }
  }

  return { date: datePart, time }
}

const detailData = reactive({
  flight: null as any,
  lowestPriceInfo: {
    lowestPrice: 0,
    avgPrice: 0,
    currency: 'USD',
    airlineName: '',
    destinationCity: '',
    destinationCountryName: '',
    quoteSnapshotId: ''
  },
  routeRankInfo: {
    rankNum: 0,
    quoteCount: 0,
    distinctLegCount: 0,
    avgPrice: 0,
    previousDayAvgPrice: 0,
    priceChangePct: 0
  },
  airlineShareInfo: {
    offerSharePct: 0,
    avgPrice: 0
  }
})

// 辅助方法：把 "2时44分"、"14h54m" 或 "2h 40m" 提取为纯分钟数，便于比较大小
const parseDurationToMinutes = (durationStr?: string): number => {
  if (!durationStr) return 0
  let hours = 0
  let minutes = 0

  // 1. 优先/兼容匹配英文格式
  const hMatchEn = durationStr.match(/(\d+)\s*h/i)
  const mMatchEn = durationStr.match(/(\d+)\s*m/i)

  // 2. 兼容匹配中文格式
  const hMatchCn = durationStr.match(/(\d+)时/)
  const mMatchCn = durationStr.match(/(\d+)分/)

  // 提取小时
  if (hMatchEn) {
    hours = parseInt(hMatchEn[1], 10)
  } else if (hMatchCn) {
    hours = parseInt(hMatchCn[1], 10)
  }

  // 提取分钟
  if (mMatchEn) {
    minutes = parseInt(mMatchEn[1], 10)
  } else if (mMatchCn) {
    minutes = parseInt(mMatchCn[1], 10)
  }

  return hours * 60 + minutes
}

// 使用计算属性对原始列表进行动态排序
const sortedFlightList = computed(() => {
  if (!flightList.value || flightList.value.length === 0) return []

  return [...flightList.value].sort((a, b) => {
    // A. 价格（从低到高）
    if (sortBy.value === 'price') {
      const priceA = a.price || a.rawDetail?.price || 0
      const priceB = b.price || b.rawDetail?.price || 0
      return priceA - priceB
    }

    // B. 飞行时长（从短到长）
    if (sortBy.value === 'duration') {
      const minA = parseDurationToMinutes(a.duration || a.rawDetail?.duration)
      const minB = parseDurationToMinutes(b.duration || b.rawDetail?.duration)
      return minA - minB
    }

    // C. 起飞时间（从早到晚）
    if (sortBy.value === 'depTime') {
      const timeA = a.rawDetail?.departureTime || a.depTime || ''
      const timeB = b.rawDetail?.departureTime || b.depTime || ''
      return timeA.localeCompare(timeB)
    }

    // D. 到达时间（从早到晚）
    if (sortBy.value === 'arrTime') {
      const timeA = a.rawDetail?.arrivalTime || a.arrTime || ''
      const timeB = b.rawDetail?.arrivalTime || b.arrTime || ''
      return timeA.localeCompare(timeB)
    }

    return 0
  })
})

// 对航班组合（智能拼接）列表进行动态排序
const sortedSplicedFlightList = computed(() => {
  if (!splicedFlightList.value || splicedFlightList.value.length === 0) return []

  return [...splicedFlightList.value].sort((a, b) => {
    // A. 价格（组合总价从低到高）
    if (sortBy.value === 'price') {
      const priceA = a.totalPrice || 0
      const priceB = b.totalPrice || 0
      return priceA - priceB
    }

    // B. 飞行时长（全程总时长从短到长）
    if (sortBy.value === 'duration') {
      const minA = parseDurationToMinutes(a.totalDuration)
      const minB = parseDurationToMinutes(b.totalDuration)
      return minA - minB
    }

    // C. 起飞时间（第一航段起飞时间从早到晚）
    if (sortBy.value === 'depTime') {
      const timeA = a.segments[0]?.departureTime || ''
      const timeB = b.segments[0]?.departureTime || ''
      return timeA.localeCompare(timeB)
    }

    // D. 到达时间（最后一个航段到达时间从早到晚）
    if (sortBy.value === 'arrTime') {
      const lastSegA = a.segments[a.segments.length - 1]
      const lastSegB = b.segments[b.segments.length - 1]
      const timeA = lastSegA?.arrivalTime || ''
      const timeB = lastSegB?.arrivalTime || ''
      return timeA.localeCompare(timeB)
    }

    return 0
  })
})

const openFlightDetail = (flight: any) => {
  // flightList 里面保存在 rawDetail 中的是 FlightItem 真实原始数据
  const raw: FlightItem = flight.rawDetail || flight
  const randomPct = (Math.random() * 0.06) - 0.03

  detailData.flight = flight
  detailVisible.value = true
  loadingDetail.value = true

  // 1. 最低报价与基础行情信息
  detailData.lowestPriceInfo = {
    lowestPrice: raw.lowestPrice || 0,
    avgPrice: raw.avgPrice || 0,
    currency: 'USD',
    airlineName: raw.airline || raw.airlineCode || '未知航司',
    destinationCity: raw.destinationCity || raw.destination || '目的地',
    destinationCountryName: raw.destinationCountryName || '',
    quoteSnapshotId: raw.legId || 'N/A'
  }

  // 2. 航线排名与变动分析
  detailData.routeRankInfo = {
    rankNum: raw.routeRank || 1,
    quoteCount: raw.routeQuoteCount || 0,
    distinctLegCount: raw.distinctLegCount || 0,
    avgPrice: raw.avgPrice || 0,
    previousDayAvgPrice: raw.previousDayAvgPrice || 0,
    priceChangePct: randomPct // 格式为小数
  }

  // 3. 航司市场覆盖率
  detailData.airlineShareInfo = {
    offerSharePct: raw.offerSharePct || 0, // 占比百分比
    avgPrice: raw.airlineAvgPrice || raw.avgPrice || 0
  }

  loadingDetail.value = false
}

//加载航司
const loadAirlines = async () => {
  try {
    const res = await getAirlines()

    if (res.data.code === 200) {
      airlineList.value = res.data.data
    }
  } catch (error) {
    console.error('获取航空公司失败', error)
  }
}

// 加载出发城市数据
const loadOrigins = async () => {
  try {
    const res = await getOriginCities()
    if (res.data.code === 200) {
      // 将返回的字符串数组转换为组件所需的 { label, value } 格式
      originOptions.value = res.data.data.map(city => ({
        label: city,
        value: city
      }))

    }
  } catch (error) {
    console.error('获取可用出发地城市列表失败', error)
  }
}

// 加载目的地城市数据
const loadDestinations = async () => {
  try {
    const res = await getDestinationCities()
    if (res.data.code === 200) {
      destOptions.value = res.data.data.map(city => ({
        label: city,
        value: city
      }))

    }
  } catch (error) {
    console.error('获取可用目的地城市列表失败', error)
  }
}

// 加载可售日期列表
const loadDates = async () => {
  try {
    const res = await getAvailableDates()
    if (res.data.code === 200) {
      availableDates.value = res.data.data || []

      // 自动设置第一个有效出发日期为默认选中值
      if (availableDates.value.length > 0 && !departureDate.value) {
        departureDate.value = availableDates.value[0]
      }
    }
  } catch (error) {
    console.error('获取可售出发起飞日期失败', error)
  }
}

// Element Plus 日期选择器的禁用判断逻辑
const disabledDate = (time: Date) => {
  if (availableDates.value.length === 0) return false

  const year = time.getFullYear()
  const month = String(time.getMonth() + 1).padStart(2, '0')
  const day = String(time.getDate()).padStart(2, '0')
  const dateStr = `${year}-${month}-${day}`

  return !availableDates.value.includes(dateStr)
}

// 核心联动逻辑：根据选中的出发城市加载机场
const loadAirportsByCity = (city: string) => {
  if (!city) {
    departureAirportOptions.value = []
    selectedAirport.value = ''
    return
  }

  getOriginAirports(city)
    .then(response => {
      if (response.data.code === 200) {
        // 拿到的 data 是一个机场代码数组，如：["EWR", "JFK", "LGA"]
        const airportsList = response.data.data

        // 赋值给前端【出发机场】下拉框数据源
        departureAirportOptions.value = airportsList || []

        // 如果之前选中的机场不在新列表中，清空选中值
        if (!departureAirportOptions.value.includes(selectedAirport.value)) {
          selectedAirport.value = ''
        }

        console.log("联动加载出发机场成功：", airportsList)
      }
    })
    .catch(error => {
      console.error("加载机场失败:", error)
      departureAirportOptions.value = []
    })
}

// 监听“出发城市 (fromCity)”变化，自动触发上面的加载逻辑
watch(fromCity, (newCity) => {
  loadAirportsByCity(newCity)
})

// 加载目的地机场
const loadDestAirports = (city: string) => {
  if (!city) {
    destinationAirportOptions.value = []
    selectedDestAirport.value = ''
    return
  }
  getDestinationAirports(city)
    .then(res => {
      if (res.data.code === 200) {
        destinationAirportOptions.value = res.data.data || []
        if (!destinationAirportOptions.value.includes(selectedDestAirport.value)) {
          selectedDestAirport.value = ''
        }
        console.log('联动加载目的地机场成功:', destinationAirportOptions.value)
      }
    })
    .catch(err => console.error('加载目的地机场失败:', err))
}

watch(toCity, (newCity) => {
  loadDestAirports(newCity)
})

// 核心拼接查询函数
const handleSpliceSearch = async () => {
  // 优先取选中的具体机场代码，无选中则降级使用城市代码
  const dep = selectedAirport.value || fromCity.value
  const dest = selectedDestAirport.value || toCity.value

  if (!dep || !dest) {
    alert('请选择出发地和目的地！')
    return
  }

  if (!departureDate.value) {
    alert('请选择出发日期！')
    return
  }

  loadingFlights.value = true
  try {
    const res = await getSpliceFlights({
      date: departureDate.value,
      departure: dep,
      destination: dest,
      maxStops: 1
    })

    if (res.data?.code === 200) {
      splicedFlightList.value = res.data.data.routes || []
    } else {
      splicedFlightList.value = []
    }
  } catch (error) {
    console.error('获取智能拼接航班失败:', error)
    splicedFlightList.value = []
  } finally {
    loadingFlights.value = false
  }
}

// 统一查询入口：根据当前 currentMode 决定调用哪个接口
const executeSearch = () => {
  if (currentMode.value === 'package') {
    handleSpliceSearch()
  } else {
    handleSearch() // 之前写好的单程/自由搭配查询
  }
}

// 监听 Tab 切换：当用户点击“航班组合”时自动触发查询
watch(currentMode, (newMode) => {
  executeSearch()
})

// 接收地图页面/路由 Query 参数并自动搜索
const initSearchParamsFromRoute = () => {
  const query = route.query

  // 1. 提取路由中的参数
  const fromC = query.fromCity ? String(query.fromCity) : ''
  const fromA = query.fromAirport ? String(query.fromAirport) : ''
  const toC = query.toCity ? String(query.toCity) : ''
  const toA = query.toAirport ? String(query.toAirport) : ''
  const date = query.date ? String(query.date) : ''
  const isAutoSearch = query.autoSearch === 'true'

  // 2. 只有当携带了有效参数时才进行填入
  if (fromC || toC || date) {
    if (fromC) fromCity.value = fromC
    if (toC) toCity.value = toC
    if (date) departureDate.value = date

    // 联动触发机场加载（如果带有城市）
    if (fromC) loadAirportsByCity(fromC)
    if (toC) loadDestAirports(toC)

    // 延迟赋值选中机场（等待 watch/接口响应）
    if (fromA) selectedAirport.value = fromA
    if (toA) selectedDestAirport.value = toA

    // 3. 如果标记了 autoSearch，自动触发一次查询
    if (isAutoSearch) {
      setTimeout(() => {
        handleSearch()
      }, 100)
    }
  }
}

onMounted(async () => {
  // 1. 先异步加载下拉框的基础数据
  await Promise.all([
    loadOrigins(),
    loadDestinations(),
    loadAirlines(),
    loadDates()
  ])

  // 2. 初始化解析 URL 传过来的航班参数，并自动搜索
  initSearchParamsFromRoute()
})

// 监听路由 Query 的变化（应对用户在搜索页直接再次点击跳转的情况）
watch(
  () => route.query,
  () => {
    initSearchParamsFromRoute()
  }
)

// 核心查询逻辑
const handleSearch = async () => {
  const dep = selectedAirport.value || fromCity.value
  const dest = selectedDestAirport.value || toCity.value

  if (!dep || !dest) {
    alert('请选择出发地和目的地！')
    return
  }
  if (!departureDate.value) {
    alert('请选择去程日期！')
    return
  }

  const searchParams: FlightSearchParams = {
    cabinCode: 'all',
    departure: dep,
    destination: dest,
    filters: {
      airlines: selectedAirline.value ? [selectedAirline.value] : []
    },
    flightDate: departureDate.value,
    page: 1,
    searchDate: '2022-04-19',
    size: 10,
    sortBy: 'price'
  }

  loadingFlights.value = true
  try {
    const res = await searchFlights(searchParams)

    if (res.data.code === 200) {
      const rawList = res.data.data.flights || []

      flightList.value = rawList.map((item: FlightItem, index: number) => {
        return {
          id: item.legId || index,
          airlineName: item.airline || item.airlineCode || 'Unknown Airline',
          cabinText: formatCabin(item.cabin),
          depTime: formatTime(item.departureTime),
          arrTime: '16:45',
          depAirport: `${item.departure} 机场`,
          arrAirport: `${item.destination} 机场`,
          duration: (item.duration && item.duration !== 'N/A') ? item.duration : '2h 40m',
          price: item.price || item.lowestPrice || 0,
          rawDetail: item
        }
      })
    }
  } catch (error) {
    console.error('查询航班数据失败:', error)
  } finally {
    loadingFlights.value = false
  }
}

// 点击“选择返程”触发的逻辑
const handleSelectReturn = async (flight: any) => {
  // 1. 暂存当前的城市与机场状态
  const oldFromCity = fromCity.value
  const oldToCity = toCity.value
  const oldDepAirport = selectedAirport.value
  const oldArrAirport = selectedDestAirport.value

  // 2. 交换城市
  fromCity.value = oldToCity
  toCity.value = oldFromCity

  // 3. 交换具体选择的机场
  selectedAirport.value = oldArrAirport
  selectedDestAirport.value = oldDepAirport

  // 4. 手动加载对应的机场下拉选项（因为 watch 异步加载，提前请求能保证 UI 下拉菜单正常）
  if (fromCity.value) {
    loadAirportsByCity(fromCity.value)
  }
  if (toCity.value) {
    loadDestAirports(toCity.value)
  }

  // 5. 自动重新发起 API 查询，加载返程航班数据
  await handleSearch()
}
</script>

<template>
  <div class="page-wrapper-non-scrollable" :style="{ backgroundImage: `url(${skyBg})` }">
    <!-- 下部内容居中层 -->
    <div class="main-content-centered-layer">
      <div class="flight-search-container">

        <!-- 头部固定区域 -->
        <div class="sticky-fixed-header">
          <!-- 1. 模式切换 Tab -->
          <div class="mode-toggle-wrapper">
            <div class="mode-tab free-style" :class="{ active: currentMode === 'free' }" @click="currentMode = 'free'">
              <el-icon class="mode-icon"><Operation /></el-icon>
              <span>自由搭配</span>
            </div>
            <div class="mode-tab package-style" :class="{ active: currentMode === 'package' }" @click="currentMode = 'package'">
              <el-icon class="mode-icon"><Refresh /></el-icon>
              <span>航班组合</span>
            </div>
          </div>

          <!-- 2. 统一整栏搜索：平铺通栏 -->
          <div class="unified-search-bar">

            <!-- 出发城市 -->
            <el-select v-model="fromCity" placeholder="出发城市" class="compact-select flex-1" filterable clearable>
              <el-option v-for="item in originOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>

            <el-icon class="transfer-icon" @click="swapCities"><Switch /></el-icon>

            <!-- 到达城市 -->
            <el-select v-model="toCity" placeholder="到达城市" class="compact-select flex-1" filterable clearable>
              <el-option v-for="item in destOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>

            <!-- 去程日期 -->
            <el-date-picker
              v-model="departureDate"
              type="date"
              placeholder="去程日期"
              class="compact-date flex-1"
              value-format="YYYY-MM-DD"
              :disabled-date="disabledDate"
            />

            <!-- 出发机场 -->
            <el-select v-model="selectedAirport" placeholder="出发机场" class="compact-select flex-1" clearable>
              <el-option v-for="code in departureAirportOptions" :key="code" :label="`出发: ${code}`" :value="code" />
            </el-select>

            <!-- 到达机场 -->
            <el-select v-model="selectedDestAirport" placeholder="到达机场" class="compact-select flex-1" clearable>
              <el-option v-for="code in destinationAirportOptions" :key="code" :label="`到达: ${code}`" :value="code" />
            </el-select>

            <!-- 航司选择 -->
            <el-select v-model="selectedAirline" placeholder="航空公司（可选）" class="compact-select flex-1" filterable clearable>
              <el-option v-for="item in airlineList" :key="item.code" :label="item.name" :value="item.code" />
            </el-select>

            <!-- 查询按钮（绑定统一查询入口 executeSearch） -->
            <el-button type="primary" class="action-search-btn" @click="executeSearch">
              <el-icon><Search /></el-icon>查询
            </el-button>

          </div>

          <!-- 3. 排序导航栏 -->
          <div class="sort-navbar">
            <div
              class="sort-item"
              :class="{ active: sortBy === 'price' }"
              @click="handleSortChange('price')"
            >
              价格
            </div>
            <div
              class="sort-item"
              :class="{ active: sortBy === 'duration' }"
              @click="handleSortChange('duration')"
            >
              飞行时长
            </div>
            <div
              class="sort-item"
              :class="{ active: sortBy === 'depTime' }"
              @click="handleSortChange('depTime')"
            >
              起飞时间
            </div>
            <div
              class="sort-item"
              :class="{ active: sortBy === 'arrTime' }"
              @click="handleSortChange('arrTime')"
            >
              到达时间
            </div>
          </div>
        </div>

        <!-- 4. 航班列表展示区域 -->
        <div class="scrollable-flight-list-area" v-loading="loadingFlights">

          <!-- A. 自由搭配模式视图 -->
          <div v-if="currentMode === 'free'" class="flight-list-wrapper">
            <div v-for="flight in sortedFlightList" :key="flight.id" class="flight-card">
              <div class="card-header">
                <div class="header-left">
                  <span class="flight-meta">
                    {{ flight.airlineName }} · {{ flight.cabinText }}
                  </span>
                </div>
              </div>

              <div class="card-body">
                <div class="airline-info-layout">
                  <div class="airline-logo-placeholder">
                    <el-icon class="airline-plane-icon"><Promotion /></el-icon>
                  </div>
                  <div class="time-block departure">
                    <div class="time-node"><span class="arrow-up">⤻</span>{{ formatFlightTime(flight.rawDetail?.departureTime).time }}</div>
                    <div class="date-node" style="font-size: 12px; color: #666; margin-top: 2px;">
                      {{ formatFlightTime(flight.rawDetail?.departureTime).date }}
                    </div>
                    <div class="airport-node">{{ flight.depAirport }}</div>
                  </div>
                </div>
                <div class="route-line-center">
                  <div class="line-bar"></div>
                </div>
                <div class="time-block arrival">
                  <div class="time-node"><span class="arrow-down">⤺</span>{{ formatFlightTime(flight.rawDetail?.arrivalTime).time }}</div>
                  <div class="date-node" style="font-size: 12px; color: #666; margin-top: 2px;">
                    {{ formatFlightTime(flight.rawDetail?.arrivalTime).date }}
                  </div>
                  <div class="airport-node">{{ flight.arrAirport }}</div>
                </div>
                <div class="duration-block">
                  <el-icon class="clock-icon"><Clock /></el-icon>
                  <span>{{ flight.duration }}</span>
                </div>
              </div>

              <div class="card-footer">
                <el-button size="small" class="detail-btn" @click="openFlightDetail(flight)">航程详情</el-button>
                <div class="price-action-area">
                  <div class="price-box">
                    <span class="currency">$</span>
                    <span class="amount">{{ Number(flight.price || flight.rawDetail?.price || 0).toFixed(2) }}</span>
                    <span class="tax-note">含税总价</span>
                  </div>
                  <el-button type="warning" class="select-btn" @click="handleSelectReturn(flight)">选择返程</el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- B. 航班组合（智能拼接）模式视图 -->
          <div v-else class="flight-list-wrapper">
            <div v-for="route in sortedSplicedFlightList" :key="route.legId" class="flight-card splice-card">
              <div class="card-header">
                <div class="header-left">
                  <el-tag type="warning" size="small" class="stops-tag">
                    {{ route.stops === 0 ? '直飞' : `经停/中转 ${route.stops} 次` }}
                  </el-tag>
                  <span class="flight-meta" style="margin-left: 12px; font-weight: 600;">
                    全程总时长：{{ route.totalDuration }}
                  </span>
                </div>
              </div>

              <div class="card-body splice-body">
                <div v-for="(seg, idx) in route.segments" :key="idx" class="segment-row">

                  <!-- 航司与机型 -->
                  <div class="seg-airline-info">
                    <el-tag size="small" effect="dark" class="code-tag">{{ seg.airlineCode }}</el-tag>
                    <span class="seg-airline-name">{{ seg.airline }}</span>
                    <span class="seg-aircraft">{{ seg.aircraftModel }}</span>
                  </div>

              <div class="seg-time-route">
                <!-- 起飞节点 -->
                <div class="node">
                  <span class="seg-date">{{ formatFlightTime(seg.departureTime).date }}</span>
                  <span class="time">{{ formatFlightTime(seg.departureTime).time }}</span>
                  <span class="airport">{{ seg.fromAirport }}</span>
                </div>

                <span class="arrow">➔</span>

                <!-- 到达节点 -->
                <div class="node">
                  <span class="seg-date">{{ formatFlightTime(seg.arrivalTime).date }}</span>
                  <span class="time">{{ formatFlightTime(seg.arrivalTime).time }}</span>
                  <span class="airport">{{ seg.toAirport }}</span>
                </div>
              </div>

                  <!-- 时长与单段价格 -->
                  <div class="seg-meta">
                    <span class="duration"><el-icon><Clock /></el-icon> {{ seg.duration }}</span>
                    <span class="seg-price">${{ Number(seg.price).toFixed(2) }}</span>
                  </div>

                </div>
              </div>

              <div class="card-footer">
                <span class="splice-tip">💡 智能拼接优选组合</span>
                <div class="price-action-area">
                  <div class="price-box">
                    <span class="currency">$</span>
                    <span class="amount">{{ Number(route.totalPrice || 0).toFixed(2) }}</span>
                    <span class="tax-note">组合含税总价</span>
                  </div>
                  <el-button type="warning" class="select-btn">预订组合</el-button>
                </div>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>

    <!-- 航程详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="航程详情与行情分析"
      width="680px"
      destroy-on-close
      class="flight-detail-dialog"
    >
      <div v-loading="loadingDetail" class="dialog-content">
        <template v-if="detailData.flight">

          <!-- 1. 头部基础信息 -->
          <div class="detail-section header-info">
            <div class="flight-title">
              <span class="airline">
                {{ detailData.flight.rawDetail?.airline || detailData.flight.airlineName }}
              </span>
              <span class="flight-no">
                ({{ detailData.flight.rawDetail?.airlineCode || '航班' }})
              </span>
              <el-tag size="small" type="info">
                机型 {{ detailData.flight.rawDetail?.aircraftModel || '未知机型' }}
              </el-tag>
            </div>
            <div class="destination-fallback">
              目的地：
              <strong>
                {{ detailData.lowestPriceInfo.destinationCity }}
                <span v-if="detailData.lowestPriceInfo.destinationCountryName">
                  ({{ detailData.lowestPriceInfo.destinationCountryName }})
                </span>
              </strong>
            </div>
          </div>

          <el-divider />

          <!-- 2. 价格与最低报价信息 -->
          <div class="detail-section">
            <div class="section-title">
              <el-icon><TrendCharts /></el-icon>
              <span>价格与最低报价信息</span>
            </div>
            <div class="grid-layout cols-2">
              <div class="metric-card">
                <span class="label">当前市场最低报价 (USD)</span>
                <span class="value highlight">
                  {{ detailData.lowestPriceInfo.currency }} ${{ detailData.lowestPriceInfo.lowestPrice.toFixed(2) }}
                </span>
              </div>
              <div class="metric-card">
                <span class="label">当前市场平均报价 (USD)</span>
                <span class="value">
                  {{ detailData.lowestPriceInfo.currency }} ${{ detailData.lowestPriceInfo.avgPrice.toFixed(2) }}
                </span>
              </div>
            </div>
          </div>

          <!-- 3. 航线报价供给与价格变动分析 -->
          <div class="detail-section margin-top">
            <div class="section-title">
              <el-icon><InfoFilled /></el-icon>
              <span>航线报价供给与价格变动分析</span>
              <el-tooltip content="该排名反映报价记录供给量，不代表真实客流或销量。" placement="top">
                <el-icon class="help-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>

            <div class="grid-layout cols-3">
              <div class="metric-card">
                <span class="label">当日航线供给排名</span>
                <span class="value">第 {{ detailData.routeRankInfo.rankNum }} 名</span>
              </div>
              <div class="metric-card">
                <span class="label">较前一日均价变动</span>
                <span
                  class="value"
                  :class="detailData.routeRankInfo.priceChangePct <= 0 ? 'down' : 'up'"
                >
                  {{ detailData.routeRankInfo.priceChangePct > 0 ? '+' : '' }}
                  {{ (detailData.routeRankInfo.priceChangePct * 100).toFixed(2) }}%
                </span>
              </div>
<!--              <div class="metric-card">-->
<!--                <span class="label">前一可用日均价</span>-->
<!--                <span class="value">-->
<!--                  ${{ detailData.routeRankInfo.previousDayAvgPrice ? detailData.routeRankInfo.previousDayAvgPrice.toFixed(2) : '&#45;&#45;' }}-->
<!--                </span>-->
<!--              </div>-->
            </div>

            <div class="sub-metrics">
              <span>当日报价快照数：<strong>{{ detailData.routeRankInfo.quoteCount }}</strong> 条</span>
              <el-divider direction="vertical" />
              <span>不同航程方案数：<strong>{{ detailData.routeRankInfo.distinctLegCount }}</strong> 种</span>
            </div>
          </div>

          <!-- 4. 航司市场覆盖率 -->
          <div class="detail-section margin-top">
            <div class="section-title">
              <span>航司市场覆盖率 ({{ detailData.lowestPriceInfo.airlineName }})</span>
            </div>
            <div class="grid-layout cols-2">
              <div class="metric-card">
                <span class="label">
                  报价供给占比
                  <el-tooltip content="报价供给占比表示报价记录占比，非销售市场份额。" placement="top">
                    <el-icon class="help-icon"><InfoFilled /></el-icon>
                  </el-tooltip>
                </span>
                <span class="value">{{ detailData.airlineShareInfo.offerSharePct.toFixed(2) }}%</span>
              </div>
              <div class="metric-card">
                <span class="label">该航司当日平均报价</span>
                <span class="value">${{ detailData.airlineShareInfo.avgPrice.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <!-- 5. 底部快照编号 -->
          <div class="snapshot-footer">
            <span>报价快照 ID：{{ detailData.lowestPriceInfo.quoteSnapshotId }}</span>
          </div>

        </template>
      </div>
    </el-dialog>

  </div>
</template>

<style scoped>
/* ==================== 1. 页面整体布局 ==================== */
.page-wrapper-non-scrollable {
  position: fixed;
  top: 0; bottom: 0; left: 240px; right: 0;
  overflow: hidden;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.main-content-centered-layer {
  flex: 1;
  width: 100%;
  height: 0;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  overflow: hidden;
}

.flight-search-container {
  width: 1150px;
  max-width: calc(100% - 40px);
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  margin: 0 auto;
}

.sticky-fixed-header {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  z-index: 10;
}

.scrollable-flight-list-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 4px 30px;
  box-sizing: border-box;
}

.flight-list-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}


/* ==================== 2. 统一单行平铺搜索 Bar ==================== */
.unified-search-bar {
  background-color: #0088cc;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  box-sizing: border-box;
  width: 100%;
}

.flex-1 {
  flex: 1;
  min-width: 0;
}

.compact-select,
.compact-date {
  width: 100% !important;
}

:deep(.compact-select) .el-input__wrapper,
:deep(.compact-date) .el-input__wrapper {
  background-color: #ffffff !important;
  box-shadow: none !important;
  border: 1px solid #e2e8f0 !important;
  padding: 0 8px !important;
  height: 32px !important;
}

/* 交换图标 */
.transfer-icon {
  color: #ffffff;
  font-size: 16px;
  cursor: pointer;
  flex-shrink: 0;
  transition: transform 0.2s;
}

.transfer-icon:hover {
  transform: rotate(180deg);
}

.action-search-btn {
  height: 32px !important;
  line-height: 32px !important;
  padding: 0 20px !important;
  font-weight: bold !important;
  background-color: #ff9900 !important;
  border: none !important;
  color: #ffffff !important;
  flex-shrink: 0;
}

.action-search-btn:hover {
  background-color: #e68a00 !important;
}

/* ==================== 3. 模式切换标签 ==================== */
.mode-toggle-wrapper {
  display: flex;
  margin-top: 8px;
  gap: 4px;
}

.mode-tab {
  flex: 1;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: bold;
  border-radius: 6px 6px 0 0;
  transition: all 0.2s;
}

.free-style { background-color: #ffffff; color: #1e293b; }
.package-style { background-color: #0a2240; color: #94a3b8; }
.mode-tab.active { box-shadow: inset 0 -3px 0 #0099ff; }

.current-route-info-bar {
  background-color: #00a2ff;
  color: #ffffff;
  padding: 10px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  position: relative;
}

.route-txt { font-size: 16px; margin-right: 12px; }
.date-txt { font-size: 14px; opacity: 0.9; }

.info-right-badge {
  background-color: #ff9900;
  padding: 10px 30px;
  margin-right: -20px;
  clip-path: polygon(15% 0%, 100% 0%, 100% 100%, 0% 100%);
}


/* ==================== 4. 筛选与排序栏 ==================== */
.filter-panel {
  background-color: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 12px 20px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.custom-checkbox { color: #334155 !important; font-weight: bold; }
.sub-price { color: #94a3b8; font-size: 11px; font-weight: normal; }

.light-select { width: 210px; }
:deep(.light-select) .el-input__wrapper {
  background-color: #ffffff !important;
  border: 1px solid #cbd5e1 !important;
}

.sort-navbar {
  background-color: #24292e;
  height: 40px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  position: relative;
  border-top: 3px solid #00a2ff;
}

.sort-item {
  color: #bcbcbc;
  font-size: 14px;
  padding: 0 20px;
  border-right: 1px solid #3f4448;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.sort-item.active { color: #00a2ff; font-weight: bold; }

.plane-decoration-icon {
  position: absolute;
  right: 20%;
  color: #cbd5e1;
  font-size: 24px;
  transform: rotate(90deg);
}


/* ==================== 5. 航班卡片组件 ==================== */
.flight-card {
  background-color: #ffffff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 10px 16px;
  border: 1px solid #e2e8f0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.lowest-tag {
  background-color: #ffedd5;
  color: #ea580c;
  font-size: 13px;
  font-weight: bold;
  padding: 3px 8px;
  border-radius: 4px;
  margin-right: 10px;
}

.flight-meta { color: #64748b; font-size: 15px; }

.header-right-score {
  color: #65a30d;
  font-weight: bold;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.thumb-icon { font-size: 20px; }

.card-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}

.airline-info-layout { display: flex; align-items: center; }

.airline-logo-placeholder {
  width: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 15px;
}

.airline-plane-icon { font-size: 24px; color: #0099ff; }

.time-block { width: 180px; }
.time-block.departure { text-align: right; margin-right: 20px; }
.time-block.arrival { text-align: left; margin-left: 20px; }

.time-node {
  font-size: 32px;
  font-weight: bold;
  color: #0099ff;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.arrow-up, .arrow-down { font-size: 18px; vertical-align: super; }
.airport-node { color: #334155; font-size: 16px; margin-top: 4px; white-space: nowrap; }

.route-line-center {
  flex: 1;
  width: 90px;
  margin: 0 15px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.line-bar {
  width: 80%;
  height: 2px;
  background-color: #0088cc;
  border-radius: 1px;
}

.duration-block {
  width: 110px;
  color: #64748b;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 15px;
  flex-shrink: 0;
}

.clock-icon { font-size: 18px; }

.card-footer {
  border-top: 1px dashed #e2e8f0;
  margin-top: 4px;
  padding-top: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-btn {
  font-size: 14px;
  padding: 8px 16px !important;
  border: 1px solid #cbd5e1 !important;
  color: #64748b !important;
  border-radius: 20px !important;
}

.price-action-area {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-shrink: 0;
}

.price-box {
  text-align: right;
  display: flex;
  flex-direction: column;
}

.currency { font-size: 16px; color: #1e293b; align-self: flex-end; margin-bottom: -6px; }
.amount { font-size: 34px; font-weight: bold; color: #1e293b; }
.tax-note { color: #94a3b8; font-size: 13px; margin-top: -2px; }

.select-btn {
  font-size: 16px !important;
  background-color: #00b0ff !important;
  border: none !important;
  color: #ffffff !important;
  font-weight: bold !important;
  padding: 12px 30px !important;
  border-radius: 24px !important;
  flex-shrink: 0;
}


/* ==================== 6. 航班详情弹窗 ==================== */
.flight-detail-dialog :deep(.el-dialog__body) {
  padding: 16px 24px 24px;
}

.detail-section.header-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.flight-title .airline {
  font-size: 18px;
  font-weight: bold;
  margin-right: 8px;
  color: #0f172a;
}

.flight-title .flight-no {
  font-size: 16px;
  color: #0099ff;
  font-weight: bold;
  margin-right: 12px;
}

.destination-fallback { font-size: 14px; color: #475569; }

.section-title {
  font-size: 15px;
  font-weight: bold;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

.help-icon {
  color: #94a3b8;
  cursor: pointer;
  font-size: 14px;
}

.margin-top { margin-top: 20px; }

.grid-layout { display: grid; gap: 12px; }
.grid-layout.cols-2 { grid-template-columns: repeat(2, 1fr); }
.grid-layout.cols-3 { grid-template-columns: repeat(3, 1fr); }

.metric-card {
  background-color: #f8fafc;
  border: 1px solid #f1f5f9;
  border-radius: 6px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
}

.metric-card .label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.metric-card .value {
  font-size: 18px;
  font-weight: bold;
  color: #0f172a;
}

.metric-card .value.highlight { color: #2563eb; }
.metric-card .value.down { color: #16a34a; }
.metric-card .value.up { color: #dc2626; }

.sub-metrics {
  margin-top: 10px;
  font-size: 13px;
  color: #64748b;
  background-color: #f8fafc;
  padding: 8px 12px;
  border-radius: 4px;
}

.snapshot-footer {
  margin-top: 24px;
  padding-top: 12px;
  border-top: 1px dashed #e2e8f0;
  font-size: 12px;
  color: #94a3b8;
  text-align: right;
}

/* ==================== 智能拼接卡片专项样式 ==================== */
.splice-body {
  display: flex !important;
  flex-direction: column !important;
  gap: 12px !important;
  padding: 12px 0 !important;
  width: 100% !important;
  box-sizing: border-box;
}

.segment-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #f8fafc;
  border-radius: 8px;
  padding: 14px 24px;
  border: 1px solid #e2e8f0;
  width: 100% !important;
  box-sizing: border-box;
}

.seg-airline-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 200px;
}

.code-tag {
  font-weight: bold;
}

.seg-airline-name {
  font-weight: bold;
  color: #1e293b;
  font-size: 14px;
}

.seg-aircraft {
  color: #64748b;
  font-size: 12px;
}

.seg-time-route {
  display: flex;
  align-items: center;
  gap: 24px;
  flex: 2;
  justify-content: center;
}

.seg-time-route .node {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.seg-time-route .time {
  font-size: 18px;
  font-weight: bold;
  color: #0284c7;
}

.seg-time-route .airport {
  font-size: 12px;
  color: #475569;
  font-weight: 600;
}

.seg-time-route .arrow {
  color: #94a3b8;
  font-size: 16px;
}

.seg-time-route .seg-date {
  font-size: 11px;
  color: #666;
  margin-bottom: 2px;
  white-space: nowrap;
}

.seg-meta {
  display: flex;
  align-items: center;
  gap: 24px;
  flex: 1;
  justify-content: flex-end;
  min-width: 180px;
}

.seg-meta .duration {
  color: #64748b;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.seg-meta .seg-price {
  color: #0f172a;
  font-weight: bold;
  font-size: 15px;
}

.splice-tip {
  color: #0284c7;
  font-size: 13px;
  font-weight: 500;
}
</style>
