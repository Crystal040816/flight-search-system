<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// 导入 API 接口
import { getOriginCities } from '@/api/origins'
import { getAvailableDates } from '@/api/dates'
import { getWhereToGo, type DestinationItem } from '@/api/gowhere'

const router = useRouter()

// --- 1. 顶栏筛选条件 ---
const fromCity = ref('')
const departureDate = ref('')
const originOptions = ref<{ label: string; value: string }[]>([])
const availableDates = ref<string[]>([])
const totalPriceSummary = ref<number | string>('--')
const loading = ref(false)

// 设置日期选择器默认焦点的面板（2022-04-19）
const defaultPickerPage = ref(new Date(2022, 3, 19))

// 15 个城市的精准经纬度映射表
const cityCoordinates: Record<string, [number, number]> = {
  'Atlanta': [33.7490, -84.3880],
  'Boston': [42.3601, -71.0589],
  'Charlotte': [35.2271, -80.8431],
  'Chicago': [41.8781, -87.6298],
  'Dallas-Fort Worth': [32.7767, -96.7970], // 修正为标准的经纬度
  'Denver': [39.7392, -104.9903],
  'Detroit': [42.3314, -83.0458],
  'Dulles': [38.9531, -77.4565],
  'Los Angeles': [34.0522, -118.2437],
  'Miami': [25.7617, -80.1918],
  'New York': [40.7128, -74.0060],
  'Newark': [40.7357, -74.1724],
  'Oakland': [37.8044, -122.2712],
  'Philadelphia': [39.9526, -75.1652],
  'San Francisco': [37.7749, -122.4194]
}

// 地图图层相关变量
let map: L.Map | null = null
const markerLayerGroup = L.layerGroup()
const destinationList = ref<DestinationItem[]>([])

// 格式化日期，防止时区偏差导致的日期偏移
const formatDate = (time: Date) => {
  const year = time.getFullYear()
  const month = String(time.getMonth() + 1).padStart(2, '0')
  const day = String(time.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 日期可选逻辑拦截
const disabledDepartureDate = (time: Date) => {
  if (!availableDates.value || availableDates.value.length === 0) return false
  const dateStr = formatDate(time)
  return !availableDates.value.includes(dateStr)
}

// --- 2. 渲染地图气泡 ---
const renderPriceMarkers = () => {
  if (!map) {
    console.warn('[Leaflet] 地图尚未初始化完成，取消打点')
    return
  }

  // 清除旧气泡
  markerLayerGroup.clearLayers()

  if (destinationList.value.length === 0) {
    console.warn('[Leaflet] 目的地列表数据为空！')
    return
  }

  destinationList.value.forEach((item) => {
    const cityName = item.city ? item.city.trim() : ''
    const coords = cityCoordinates[cityName]

    if (!coords) {
      console.error(`[Leaflet] 映射表中未找到城市名称: "${cityName}"`)
      return
    }

    const htmlContent = `
      <div class="custom-price-marker">
        <div class="location-pin-wrapper">
          <svg class="location-svg" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="currentColor"/>
            <circle cx="12" cy="9" r="3" fill="#ffffff"/>
          </svg>
          <div class="pin-line"></div>
        </div>
        <div class="price-bubble-body">
          <span class="city-code">${item.city} (${item.destination})</span>
          <span class="price-amount">$ ${item.lowestPrice}</span>
        </div>
      </div>
    `

    const customIcon = L.divIcon({
      html: htmlContent,
      className: 'custom-leaflet-icon-wrapper',
      iconSize: [110, 45],
      iconAnchor: [55, 45]
    })

    const marker = L.marker(coords, { icon: customIcon })
    marker.on('click', () => handleMarkerClick(item))
    markerLayerGroup.addLayer(marker)
  })

  // 确保图层组加在地图上
  if (!map.hasLayer(markerLayerGroup)) {
    markerLayerGroup.addTo(map)
  }
}

// map2.vue 中的跳转逻辑
const handleMarkerClick = (target: DestinationItem) => {
  console.log('点击气泡跳转航班搜索:', target)

  router.push({
    path: '/search', // 请根据你的实际搜索页路由 path 调整（如 /flight-search）
    query: {
      fromCity: target.departureCity, // 出发城市 (例如: Atlanta)
      fromAirport: target.departure,  // 出发机场三字码 (例如: ATL)
      toCity: target.city,            // 目的城市 (例如: Newark)
      toAirport: target.destination,  // 目的机场三字码 (例如: EWR)
      date: departureDate.value,      // 出发日期 (例如: 2022-04-19)
      autoSearch: 'true'              // 自动触发搜索标识
    }
  })
}

const handleSearch = async () => {
  // 1. 兜底默认参数（确保一定会传参）
  const payload = {
    departureCity: fromCity.value || 'Atlanta',
    date: departureDate.value || '2022-04-19'
  }

  console.log('发起接口请求 /api/destinations，请求体为:', payload)

  loading.value = true
  try {
    const res = await getWhereToGo(payload)
    console.log('后端完整响应结果:', res)

    if (res.data?.code === 200 && res.data.data) {
      destinationList.value = res.data.data.destinations || []

      console.log(`获取到 ${destinationList.value.length} 条目的地数据`)

      // 计算最低全网价
      if (destinationList.value.length > 0) {
        const minPrice = Math.min(...destinationList.value.map(d => d.lowestPrice))
        totalPriceSummary.value = minPrice
      } else {
        totalPriceSummary.value = '--'
      }

      // 重新渲染气泡
      renderPriceMarkers()
    } else {
      console.warn('接口返回成功，但 code 不是 200 或 data 为空:', res.data)
    }
  } catch (error) {
    console.error('获取地图目的地数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 初始化下拉菜单数据
const loadOrigins = async () => {
  try {
    const res = await getOriginCities()
    if (res.data?.code === 200) {
      originOptions.value = res.data.data.map((city: string) => ({ label: city, value: city }))
      if (originOptions.value.length > 0 && !fromCity.value) {
        fromCity.value = originOptions.value[0].value
      }
    }
  } catch (e) {
    console.error('获取出发城市失败', e)
    fromCity.value = 'Atlanta' // 兜底默认值
  }
}

const loadDates = async () => {
  try {
    const res = await getAvailableDates()
    if (res.data?.code === 200) {
      availableDates.value = res.data.data || []
      if (availableDates.value.length > 0 && !departureDate.value) {
        departureDate.value = availableDates.value[0]
      }
    }
  } catch (e) {
    console.error('获取可选日期失败', e)
    departureDate.value = '2022-04-19' // 兜底默认值
  }
}

onMounted(() => {
  // 1. 优先创建初始化地图容器，防止页面卡阻塞
  map = L.map('map-container', {
    center: [38.0000, -96.0000],
    zoom: 4,
    zoomControl: false,
    minZoom: 3,
    maxZoom: 9
  })

  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Esri Ocean',
    maxZoom: 13
  }).addTo(map)

  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Reference/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 13
  }).addTo(map)

  // 2. 并行加载配置数据并直接调取接口
  Promise.all([loadOrigins(), loadDates()]).finally(() => {
    handleSearch()
  })
})

onUnmounted(() => {
  if (map) map.remove()
})
</script>

<template>
  <div class="page-wrapper-non-scrollable">
    <!-- 顶部核心搜索栏：仅保留 出发城市 与 出发日期 -->
    <div class="search-sticky-bar">
      <!-- 出发城市下拉 -->
      <el-select
        v-model="fromCity"
        placeholder="出发城市"
        class="dark-select medium-width"
        filterable
      >
        <el-option
          v-for="item in originOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>

      <!-- 单选出发日期 -->
      <el-date-picker
        v-model="departureDate"
        type="date"
        placeholder="出发日期"
        class="dark-date-picker"
        value-format="YYYY-MM-DD"
        :disabled-date="disabledDepartureDate"
        :default-value="defaultPickerPage"
      />

      <div class="summary-total-price-box">
        <span class="label">最低全网价($)：</span>
        <span class="price-val">{{ totalPriceSummary }}</span>
      </div>

      <el-button type="primary" class="search-btn" :loading="loading" @click="handleSearch">
        <el-icon><Search /></el-icon>筛选
      </el-button>
    </div>

    <!-- 地图核心视图 -->
    <div class="map-layout-wrapper">
      <div id="map-container" class="map-core-content-blue-style"></div>
    </div>
  </div>
</template>

<style scoped>
/* ==================== 基础框架与顶栏样式 ==================== */
.page-wrapper-non-scrollable {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 240px;
  right: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background-color: #b3d1ff;
}

.search-sticky-bar {
  width: 100% !important;
  background-color: #171d26;
  padding: 0 24px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  box-sizing: border-box;
  flex-shrink: 0;
  border-bottom: 1px solid #2d3748;
  z-index: 999;
}

.search-sticky-bar :deep(.el-input__wrapper) { height: 32px !important; }
.search-btn { height: 32px !important; line-height: 32px !important; padding: 0 20px !important; }

:deep(.dark-select) .el-input__wrapper,
:deep(.dark-input) .el-input__wrapper { background-color: #262f3d !important; box-shadow: none !important; }
:deep(.dark-select) .el-input__inner,
:deep(.dark-input) .el-input__inner { color: #38bdf8 !important; font-weight: bold; }
.medium-width { width: 150px; }

:deep(.dark-date-picker) { background-color: #262f3d !important; border: none !important; width: 160px !important; }
:deep(.dark-date-picker) .el-input__inner { color: #38bdf8 !important; font-weight: bold; }

.summary-total-price-box { display: flex; align-items: center; margin-left: 10px; font-size: 14px; }
.summary-total-price-box .label { color: #a0aec0; }
.summary-total-price-box .price-val { color: #f6ad55; font-size: 20px; font-weight: bold; }

.map-layout-wrapper { flex: 1; width: 100%; height: 0; position: relative; }
.map-core-content-blue-style { width: 100%; height: 100%; z-index: 1; filter: hue-rotate(5deg) contrast(105%) saturate(110%); }
:deep(.leaflet-container) { background: #b3d1ff !important; }

/* ==================== 气泡 Marker 样式 ==================== */
:deep(.custom-leaflet-icon-wrapper) {
  overflow: visible !important;
  background: none !important;
  border: none !important;
}

:deep(.custom-price-marker) {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: transform 0.15s ease;
}

:deep(.custom-price-marker:hover) {
  transform: scale(1.08);
  z-index: 9999 !important;
}

:deep(.location-pin-wrapper) {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #ff7597;
  filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.12));
}

:deep(.location-svg) {
  width: 20px;
  height: 20px;
}

:deep(.pin-line) {
  width: 1.5px;
  height: 6px;
  background-color: #ff7597;
  margin-top: -1px;
}

:deep(.price-bubble-body) {
  background-color: #ff7597;
  color: #ffffff;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: bold;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 3px 8px rgba(255, 117, 151, 0.3);
  min-width: 80px;
  text-align: center;
  line-height: 1.2;
}

:deep(.city-code) {
  font-size: 11px;
  font-weight: normal;
  white-space: nowrap;
}

:deep(.price-amount) {
  font-size: 14px;
  font-weight: 800;
  margin-top: 2px;
}
</style>
