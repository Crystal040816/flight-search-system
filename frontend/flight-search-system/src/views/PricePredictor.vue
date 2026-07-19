<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ArrowRight } from '@element-plus/icons-vue'
import skyBg from '../pictures/天空.jpg'

// --- 1. 顶栏筛选状态 ---
const fromCity = ref('巴黎 (PAR)')
const toCity = ref('纽约 (NYC)')
const directOnly = ref(true)
const cabinType = ref('经济舱')

const selectedMonth = ref('八月')

// --- 2. 模拟数据 ---
const monthData = [
  { name: '六月', price: 1813 },
  { name: '七月', price: 2428 },
  { name: '八月', price: 1920, isLowest: true },
  { name: '九月', price: 1803 }
]

const generateDaysData = (highlightDay: number) => {
  return Array.from({ length: 31 }, (_, i) => {
    const day = i + 1
    const hasFlight = Math.random() > 0.1
    let price = hasFlight ? Math.floor(Math.random() * 2500) + 1800 : null
    if (day === highlightDay) price = 2200
    return {
      day,
      weekday: ['三', '四', '五', '六', '日', '一', '二'][i % 7],
      price
    }
  })
}

const departureDays = ref(generateDaysData(24))
const returnDays = ref(generateDaysData(10))

// --- 3. ECharts 引用 ---
const monthChartRef = ref<HTMLElement | null>(null)
const departureChartRef = ref<HTMLElement | null>(null)
const returnChartRef = ref<HTMLElement | null>(null)

let monthChart: echarts.ECharts | null = null
let departureChart: echarts.ECharts | null = null
let returnChart: echarts.ECharts | null = null

// --- 4. 核心：构建 ECharts 配置 ---
const initMonthChart = () => {
  if (!monthChartRef.value) return
  monthChart = echarts.init(monthChartRef.value)

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', show: false },
    grid: { top: 60, bottom: 30, left: 50, right: 50, containLabel: true },
    xAxis: {
      type: 'category',
      data: monthData.map(d => d.name),
      axisLine: { lineStyle: { color: '#4a5568' } },
      axisLabel: { color: '#a0aec0', fontSize: 13, margin: 15 },
      boundaryGap: true
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 3500,
      interval: 1000,
      axisLabel: {
        color: '#a0aec0',
        formatter: (val: number) => val === 0 ? '¥0' : `¥${val}`
      },
      splitLine: { lineStyle: { color: 'rgba(74, 85, 104, 0.2)' } }
    },
    series: [
      {
        type: 'line',
        data: monthData.map(d => d.price),
        lineStyle: { color: '#ff7597', width: 3 },
        itemStyle: { color: '#1a202c', borderColor: '#ff7597', borderWidth: 3 },
        symbol: 'circle',
        symbolSize: 14,
        label: {
          show: true,
          position: 'top',
          offset: [0, -10],
          formatter: (params: any) => {
            const item = monthData[params.dataIndex]
            if (item.name === selectedMonth.value) {
              return `{lowestTitle|最低价}\n{lowestPrice|¥ ${item.price.toLocaleString()}}`
            }
            return `{normalBox|¥ ${item.price.toLocaleString()}}`
          },
          rich: {
            lowestTitle: { backgroundColor: '#0f172a', color: '#ffffff', padding: [2, 10], borderRadius: [2, 2, 0, 0], fontSize: 10, align: 'center' },
            lowestPrice: { backgroundColor: '#f59e0b', color: '#ffffff', padding: [4, 10], borderRadius: [0, 0, 2, 2], fontWeight: 'bold', fontSize: 12, align: 'center' },
            normalBox: { backgroundColor: '#3182ce', color: '#ffffff', padding: [4, 8], borderRadius: 3, fontSize: 11, fontWeight: 'bold' }
          }
        }
      },
      {
        type: 'bar',
        data: monthData.map(d => d.price),
        barWidth: 1,
        itemStyle: { color: 'rgba(217, 119, 6, 0.5)' },
        z: 1
      }
    ]
  }
  monthChart.setOption(option)

  monthChart.on('click', (params) => {
    selectedMonth.value = monthData[params.dataIndex].name
    departureDays.value = generateDaysData(Math.floor(Math.random() * 25) + 3)
    returnDays.value = generateDaysData(Math.floor(Math.random() * 25) + 3)
    initMonthChart()
    initBarCharts()
  })
}

const renderBarChart = (chartInstance: echarts.ECharts | null, el: HTMLElement, dataSource: any[], highlightDay: number) => {
  // 如果容器没有渲染成功，先跳过
  if (!el.clientWidth) return null
  if (!chartInstance) chartInstance = echarts.init(el)

  const option = {
    backgroundColor: 'transparent',
    grid: { top: 30, bottom: 45, left: 50, right: 20 },
    xAxis: {
      type: 'category',
      data: dataSource.map(d => d.day),
      axisLine: { lineStyle: { color: '#4a5568' } },
      axisLabel: {
        interval: 0,
        color: '#a0aec0',
        fontSize: 10,
        formatter: (value: string, index: number) => {
          const item = dataSource[index]
          return `${value}\n{wk|${item.weekday}}`
        },
        rich: { wk: { color: '#718096', fontSize: 9, padding: [3, 0, 0, 0] } }
      }
    },
    yAxis: {
      type: 'value',
      max: 5000,
      splitLine: { lineStyle: { color: 'rgba(74, 85, 104, 0.15)' } },
      axisLabel: { color: '#718096', fontSize: 10 }
    },
    series: [
      {
        type: 'bar',
        barWidth: '70%',
        data: dataSource.map((d) => {
          if (d.price === null) return 0
          const color = d.day === highlightDay ? '#ff7597' : '#d97706'
          return {
            value: d.price,
            itemStyle: { color: color, borderRadius: [1, 1, 0, 0] }
          }
        })
      }
    ]
  }
  chartInstance.setOption(option)
  return chartInstance
}

const initBarCharts = () => {
  if (departureChartRef.value) {
    departureChart = renderBarChart(departureChart, departureChartRef.value, departureDays.value, 24)
  }
  if (returnChartRef.value) {
    returnChart = renderBarChart(returnChart, returnChartRef.value, returnDays.value, 10)
  }
}

const handleResize = () => {
  monthChart?.resize()
  departureChart?.resize()
  returnChart?.resize()
}

onMounted(async () => {
  await nextTick()
  initMonthChart()
  initBarCharts()

  setTimeout(() => {
    handleResize()
  }, 100)

  window.addEventListener('resize', handleResize)
})
</script>

<template>
<div class="predictor-container" :style="{ backgroundImage: `linear-gradient(rgba(11, 15, 23, 0.8), rgba(11, 15, 23, 0.8)), url(${skyBg})` }">
    <!-- 1. 顶部筛选控制栏 -->
    <div class="top-filter-navigation">
      <div class="icon-clock-box">🕒</div>

      <div class="inputs-row">
        <el-input v-model="fromCity" class="dark-nav-input" />
        <el-input v-model="toCity" class="dark-nav-input" />

        <el-checkbox v-model="directOnly" class="dark-checkbox">直飞</el-checkbox>

        <el-select v-model="cabinType" class="dark-nav-select">
          <el-option label="经济舱" value="经济舱" />
        </el-select>
      </div>
    </div>

    <!-- 2. 上方卡片：月份总览趋势 -->
    <div class="section-card month-trend-card">
      <div class="card-title-bar">
        <div class="status-badge-green">✓</div>
        <div class="title-text">已选: {{ selectedMonth }}</div>
        <div class="route-info-tags">
          <span>{{ fromCity }}</span>
          <el-icon class="exchange-icon"><ArrowRight /></el-icon>
          <span>{{ toCity }}</span>
        </div>
      </div>
      <div ref="monthChartRef" class="chart-canvas-body"></div>
    </div>

    <!-- 3. 下方双列网格布局：启程/返程 -->
    <div class="bottom-charts-grid">
      <!-- 启程日期选择 -->
      <div class="section-card calendar-picker-card">
        <div class="card-title-bar has-step-badge">
          <div class="step-badge-pink">2</div>
          <div class="step-title">启程</div>
          <div class="route-sub-text">{{ fromCity }} ➔ {{ toCity }}</div>
        </div>
        <div class="sub-hint-text">请选择您的 启程日期</div>
        <div ref="departureChartRef" class="chart-canvas-body-sm"></div>
      </div>

      <!-- 返程日期选择 -->
      <div class="section-card calendar-picker-card">
        <div class="card-title-bar has-step-badge">
          <div class="step-badge-pink">3</div>
          <div class="step-title">返程</div>
          <div class="route-sub-text">{{ toCity }} ➔ {{ fromCity }}</div>
        </div>
        <div class="sub-hint-text">请选择您的 返程日期</div>
        <div ref="returnChartRef" class="chart-canvas-body-sm"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.predictor-container {
position: fixed;
  top: 0;
  bottom: 0;
  right: 0;
  left: 240px;

  height: 100vh !important;
  box-sizing: border-box;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
  z-index: 10;

  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.top-filter-navigation,
.month-trend-card,
.bottom-charts-grid {
  width: 100% !important;
  max-width: none !important;
  box-sizing: border-box;
}

.inputs-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

:deep(.dark-nav-input) .el-input__wrapper {
  background-color: #1f2937 !important;
  box-shadow: none !important;
  border: 1px solid #374151;
  height: 30px;
  width: 140px;
}
:deep(.dark-nav-input) .el-input__inner {
  color: #38bdf8 !important;
  font-weight: 600;
}
:deep(.dark-checkbox) {
  color: #9ca3af !important;
}
:deep(.dark-nav-select) .el-input__wrapper {
  background-color: #1f2937 !important;
  box-shadow: none !important;
  border: 1px solid #374151;
  height: 30px;
  width: 90px;
}

.section-card {
  background-color: rgba(19, 25, 36, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
}

.month-trend-card {
  flex: 1.2;
  padding: 16px;
  min-height: 0;
}

.card-title-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(51, 65, 85, 0.3);
  padding-bottom: 10px;
  flex-shrink: 0;
}

.status-badge-green {
  background-color: #10b981;
  color: #ffffff;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
}

.title-text {
  font-size: 14px;
  font-weight: bold;
}

.route-info-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #a0aec0;
}

.chart-canvas-body,
.chart-canvas-body-sm {
  width: 100%;
  flex: 1;
  min-height: 0;
}

.bottom-charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.calendar-picker-card {
  height: 100%;
  padding: 0;
  overflow: hidden;
}

.card-title-bar.has-step-badge {
  padding: 0;
  height: 42px;
  border-bottom: none;
  background-color: rgba(24, 34, 50, 0.9);
  flex-shrink: 0;
}

.step-badge-pink {
  background-color: #ff7597;
  color: #ffffff;
  width: 45px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 900;
}

.step-title {
  font-size: 14px;
  font-weight: bold;
}

.route-sub-text {
  font-size: 12px;
  color: #94a3b8;
  margin-left: auto;
  padding-right: 16px;
}

.sub-hint-text {
  text-align: center;
  color: #64748b;
  font-size: 12px;
  margin-top: 10px;
  flex-shrink: 0;
}

.chart-canvas-body-sm {
  width: 100%;
  flex: 1;
  min-height: 0;
  padding-bottom: 5px;
}
</style>
