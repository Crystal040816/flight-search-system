<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const router = useRouter()

// --- 1. 顶部搜索栏状态 ---
const tripType = ref('往返')
const passengers = ref('1人, 经济舱')
const fromCity = ref('香港 (HKG)')
const dateRange = ref(['2026-03-09', '2026-03-16'])
const totalPriceSummary = ref(1030) // 联动显示的往返最低总价

let map: L.Map | null = null
// 用一个数组存储当前地图上的所有 Marker，方便切换数据时清除旧标记
const markerLayerGroup = L.layerGroup()

// --- 2. 模拟各个目的地的低价数据集 (实际开发中由后端 API 根据出发地和时间返回) ---
const destinationLowPrices = ref([
  { city: '西安 (SIA)', lat: 34.3416, lng: 108.9398, price: 1230, isLowest: false },
  { city: '首尔 (ICN)', lat: 37.5665, lng: 126.9780, price: 1518, isLowest: true, count: 3 },
  { city: '东京 (NRT)', lat: 35.6762, lng: 139.6503, price: 1738, isLowest: true, count: 2 },
  { city: '台北 (TPE)', lat: 25.0330, lng: 121.5654, price: 1240, isLowest: false },
  { city: '澳门 (MFM)', lat: 22.1987, lng: 113.5439, price: 2233, isLowest: false },
  { city: '河内 (HAN)', lat: 21.0285, lng: 105.8542, price: 1124, isLowest: false },
  { city: '曼谷 (BKK)', lat: 13.7563, lng: 100.5018, price: 1240, isLowest: true, count: 2 },
  { city: '马尼拉 (MNL)', lat: 14.5995, lng: 120.9842, price: 1070, isLowest: true },
  { city: '胡志明市 (SGN)', lat: 10.8231, lng: 106.6297, price: 1401, isLowest: false },
  { city: '吉隆坡 (KUL)', lat: 3.1390, lng: 101.6869, price: 2256, isLowest: true },
  { city: '哥打京那巴鲁 (BKI)', lat: 5.9788, lng: 116.0753, price: 1510, isLowest: false },
  { city: '新加坡 (SIN)', lat: 1.3521, lng: 103.8198, price: 1030, isLowest: true, count: 2 },
  { city: '雅加达 (JKT)', lat: -6.2088, lng: 106.8456, price: 1995, isLowest: false },
  { city: '达卡 (DAC)', lat: 23.8103, lng: 90.4125, price: 2636, isLowest: false }
])

// --- 3. 核心：在地图上绘制机票低价气泡 ---
const renderPriceMarkers = () => {
  if (!map) return

  // 先清空上一次的旧标记
  markerLayerGroup.clearLayers()

  destinationLowPrices.value.forEach((item) => {
    const lowestBadge = item.isLowest ? `<div class="badge-lowest">LOWEST</div>` : ''
    const countBadge = item.count ? `<div class="badge-count">${item.count}</div>` : ''


const htmlContent = `
  <div class="custom-price-marker">
    <!-- 统一的 Location Logo (SVG) -->
    <div class="location-pin-wrapper">
      <svg class="location-svg" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="currentColor"/>
        <circle cx="12" cy="9" r="3" fill="#ffffff"/>
      </svg>
      <div class="pin-line"></div>
    </div>

    <!-- 机票最低价格主体 -->
    <div class="price-bubble-body">
      <span class="city-code">${item.city.split(' ')[0]}</span>
      <span class="price-amount">¥ ${item.price.toLocaleString()}</span>
    </div>
  </div>
`
    // 创建 Leaflet 自定义 divIcon
    const customIcon = L.divIcon({
      html: htmlContent,
      className: 'custom-leaflet-icon-wrapper', // 抹平默认样式
      iconSize: [100, 40],
      iconAnchor: [50, 40] // 让气泡底部中心对准经纬度坐标
    })

    // 创建标记并绑定点击事件
    const marker = L.marker([item.lat, item.lng], { icon: customIcon })

    marker.on('click', () => {
      handleMarkerClick(item)
    })

    markerLayerGroup.addLayer(marker)
  })

  markerLayerGroup.addTo(map)
}

// --- 4. 业务逻辑：点击气泡，带参数跳转至“机票详情页” ---
const handleMarkerClick = (targetDestination: any) => {
  console.log(`用户点击了目的地: ${targetDestination.city}，准备进入实时搜索...`)

  // 携带当前筛选条件跳转回 FlightSearch.vue 页面
  router.push({
    path: '/search',
    query: {
      from: fromCity.value,
      to: targetDestination.city,
      start: dateRange.value ? dateRange.value[0] : '',
      end: dateRange.value ? dateRange.value[1] : '',
      autoSearch: 'true' // 告诉机票页：“一进来就自动触发查询API”
    }
  })
}

// --- 5. 点击顶部筛选按钮：模拟后端数据刷新 ---
const handleSearch = () => {
  console.log('触发新条件下的低价分析...', fromCity.value, dateRange.value)

  // 模拟数据策略：如果出发地变了，就随机变动一下价格列表
  destinationLowPrices.value = destinationLowPrices.value.map(item => ({
    ...item,
    price: item.price + Math.floor((Math.random() - 0.5) * 300)
  }))

  // 找出新的全网最低价更新到右侧顶栏
  const minPrice = Math.min(...destinationLowPrices.value.map(o => o.price))
  totalPriceSummary.value = minPrice

  // 重新渲染气泡
  renderPriceMarkers()
}

onMounted(() => {
  // 初始化地图
  map = L.map('map-container', {
    center: [15.0000, 115.0000], // 稍微居中，方便容纳东南亚及东亚全景
    zoom: 4,
    zoomControl: false,
    minZoom: 3,
    maxZoom: 9
  })

  // 注入蓝白底图
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Esri Ocean',
    maxZoom: 13
  }).addTo(map)

  // 注入地名边界
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Reference/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 13
  }).addTo(map)

  // 初始渲染气泡
  renderPriceMarkers()
})

onUnmounted(() => {
  if (map) map.remove()
})
</script>

<template>
  <div class="page-wrapper-non-scrollable">
    <!-- 顶部核心搜索栏 -->
    <div class="search-sticky-bar">
      <el-select v-model="tripType" class="dark-select mini-width">
        <el-option label="往返" value="往返" />
        <el-option label="单程" value="单程" />
      </el-select>

      <el-select v-model="passengers" class="dark-select medium-width">
        <el-option label="1人, 经济舱" value="1人, 经济舱" />
      </el-select>

      <div class="route-input-group">
        <el-input v-model="fromCity" placeholder="出发城市" class="dark-input" />
      </div>

      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="去程"
        end-placeholder="返程"
        class="dark-date-picker"
        value-format="YYYY-MM-DD"
      />

      <div class="summary-total-price-box">
        <span class="label">往返总价(¥)：</span>
        <span class="price-val">{{ totalPriceSummary }}</span>
      </div>

      <el-button type="primary" class="search-btn" @click="handleSearch">
        <el-icon><Search /></el-icon>筛选
      </el-button>
    </div>

    <!-- 地图与悬浮控制组件区域 -->
    <div class="map-layout-wrapper">
      <div class="map-left-floating-toolbar">
        <div class="tool-btn active"><i class="el-icon-search">🔍</i></div>
        <div class="tool-btn">🏢</div>
        <div class="tool-btn">🗺️</div>
        <div class="tool-btn">❤️</div>
        <div class="tool-btn">✈️</div>
        <div class="tool-btn">🧳</div>
      </div>

      <!-- 左上角过滤状态提示 -->
      <div class="map-top-status-hint">
        <span>70 条航班被过滤了</span>
        <div class="refresh-sub-btn">🔄</div>
      </div>

      <!-- 地图容器 -->
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
.mini-width { width: 80px; }
.medium-width { width: 130px; }
.route-input-group { display: flex; align-items: center; background-color: #262f3d; border-radius: 4px; padding: 0 4px; }
.route-input-group .dark-input { width: 120px; }
:deep(.dark-date-picker) { background-color: #262f3d !important; border: none !important; width: 240px !important; }
:deep(.dark-date-picker) .el-range-input { color: #38bdf8 !important; font-weight: bold; }
.summary-total-price-box { display: flex; align-items: center; margin-left: 10px; font-size: 14px; }
.summary-total-price-box .label { color: #a0aec0; }
.summary-total-price-box .price-val { color: #f6ad55; font-size: 20px; font-weight: bold; }

.map-layout-wrapper { flex: 1; width: 100%; height: 0; position: relative; }
.map-core-content-blue-style { width: 100%; height: 100%; z-index: 1; filter: hue-rotate(5deg) contrast(105%) saturate(110%); }
:deep(.leaflet-container) { background: #b3d1ff !important; }

/* ==================== 界面悬浮面板 UI ==================== */
.map-left-floating-toolbar {
  position: absolute;
  left: 16px;
  top: 75px;
  z-index: 99;
  background-color: #ffffff;
  border-radius: 6px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  padding: 4px;
  border: 1px solid #cbd5e1;
}
.tool-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 18px;
  border-radius: 4px;
  color: #475569;
}
.tool-btn:hover, .tool-btn.active { background-color: #f1f5f9; color: #000; font-weight: bold; }

.map-top-status-hint {
  position: absolute;
  left: 70px;
  top: 20px;
  z-index: 99;
  background-color: rgba(15, 23, 42, 0.85);
  color: #ffffff;
  padding: 6px 14px;
  border-radius: 4px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  backdrop-filter: blur(4px);
}
.refresh-sub-btn { cursor: pointer; color: #38bdf8; }
/* ==================== 全局低价气泡 ==================== */
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
  transform: scale(1.05);
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
  width: 22px;
  height: 22px;
}

:deep(.pin-line) {
  width: 1.5px;
  height: 8px;
  background-color: #ff7597;
  margin-top: -1px;
}

:deep(.price-bubble-body) {
  background-color: #ff7597;
  color: #ffffff;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: bold;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 3px 8px rgba(255, 117, 151, 0.3); /* 干净利落的粉色投影 */
  min-width: 75px;
  text-align: center;
  line-height: 1.3;
}

:deep(.city-code) {
  font-size: 12px;
  font-weight: normal;
  letter-spacing: 0.5px;
}

:deep(.price-amount) {
  font-size: 15px;
  font-weight: 800;
  margin-top: 2px;
}
</style>
