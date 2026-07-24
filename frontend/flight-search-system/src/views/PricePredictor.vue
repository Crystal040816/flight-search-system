<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { Search, Switch } from '@element-plus/icons-vue'
import skyBg from '../pictures/天空.jpg'

// 导入 API 接口
import { postApiPredict } from '@/api/predict'
import { getOriginCities } from '@/api/origins'
import { getDestinationCities } from '@/api/destinations'
import { getAvailableDates } from '@/api/dates'

// 1. 响应式数据定义
const predictDays = ref<number>(7) // 预测未来 n 天 (默认 7)

const originOptions = ref<{ label: string; value: string }[]>([])
const destOptions = ref<{ label: string; value: string }[]>([])

const fromCity = ref('')
const toCity = ref('')
const departureDate = ref('')
const returnDate = ref('')
const availableDates = ref<string[]>([])

const loading = ref(false)

// 去程/返程预测结果
const departureSuggestion = ref('')
const departureBestBuy = ref<{ date: string; price: number } | null>(null)
const departureTrend = ref<any[]>([])

const returnSuggestion = ref('')
const returnBestBuy = ref<{ date: string; price: number } | null>(null)
const returnTrend = ref<any[]>([])

// 图表 DOM 引用与实例
const departureChartRef = ref<HTMLElement | null>(null)
const returnChartRef = ref<HTMLElement | null>(null)

let departureChart: echarts.ECharts | null = null
let returnChart: echarts.ECharts | null = null

// 2. 辅助函数
// 互换出发地和目的地
const swapCities = () => {
  const temp = fromCity.value
  fromCity.value = toCity.value
  toCity.value = temp
}

// 渲染单个 ECharts 预测折线图
const renderPredictChart = (
  chartInstance: echarts.ECharts | null,
  el: HTMLElement,
  trendList: any[],
  title: string
) => {
  if (!el || !el.parentNode || !el.clientWidth) return chartInstance

  if (!chartInstance) {
    chartInstance = echarts.init(el)
  }

  const xAxisData = trendList.map(item => item.date)
  const priceData = trendList.map(item => item.predictedPrice)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const item = params[0]
        return `日期: ${item.name}<br/>预测票价: <b>$${item.value}</b>`
      }
    },
    grid: { top: 30, bottom: 25, left: 50, right: 30, containLabel: true },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLine: { lineStyle: { color: '#4a5568' } },
      axisLabel: { color: '#a0aec0', fontSize: 11, rotate: 30 }
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        color: '#a0aec0',
        formatter: (val: number) => `$${val}`
      },
      splitLine: { lineStyle: { color: 'rgba(74, 85, 104, 0.2)' } }
    },
    series: [
      {
        name: title,
        type: 'line',
        smooth: true,
        data: priceData,
        lineStyle: { color: '#38bdf8', width: 3 },
        itemStyle: { color: '#38bdf8', borderColor: '#ffffff', borderWidth: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(56, 189, 248, 0.4)' },
            { offset: 1, color: 'rgba(56, 189, 248, 0.0)' }
          ])
        }
      }
    ]
  }

  chartInstance.setOption(option)
  return chartInstance
}

const updateCharts = () => {
  nextTick(() => {
    if (departureChartRef.value) {
      departureChart = renderPredictChart(
        departureChart,
        departureChartRef.value,
        departureTrend.value,
        '去程预测趋势'
      )
    }
    if (returnChartRef.value) {
      returnChart = renderPredictChart(
        returnChart,
        returnChartRef.value,
        returnTrend.value,
        '返程预测趋势'
      )
    }
  })
}

// 3. 核心 API 数据交互
const handleSearch = async () => {
  if (!departureDate.value || !fromCity.value || !toCity.value) return

  loading.value = true

  // 清设初始状态，避免上次查询残余干扰
  departureTrend.value = []
  returnTrend.value = []
  departureSuggestion.value = ''
  returnSuggestion.value = ''
  departureBestBuy.value = null
  returnBestBuy.value = null

  try {
    // 1. 去程预测
    const depParams = {
      days: predictDays.value,
      departure: fromCity.value,
      destination: toCity.value,
      flightDate: departureDate.value
    }

    const depRes = await postApiPredict(depParams)
    if (depRes.data?.code === 200 && depRes.data.data) {
      const data = depRes.data.data
      departureSuggestion.value = data.suggestion || ''
      departureBestBuy.value = data.bestBuy || null

      // 统一清洗去程趋势数据，防止字段未定义
      departureTrend.value = (data.trend || []).map((item: any) => ({
        date: item.date,
        predictedPrice: item.predictedPrice ?? item.predicted_price ?? 0
      }))
    }

    // 2. 返程预测 (有选择返程日期时触发)
    if (returnDate.value) {
      const retParams = {
        days: predictDays.value,
        departure: toCity.value,       // 出发目的地对调
        destination: fromCity.value,
        flightDate: returnDate.value
      }

      const retRes = await postApiPredict(retParams)
      if (retRes.data?.code === 200 && retRes.data.data) {
        const data = retRes.data.data
        returnSuggestion.value = data.suggestion || ''
        returnBestBuy.value = data.bestBuy || null

        // 统一清洗返程趋势数据
        returnTrend.value = (data.trend || []).map((item: any) => ({
          date: item.date,
          predictedPrice: item.predictedPrice ?? item.predicted_price ?? 0
        }))
      }
    }
  } catch (error) {
    console.error('获取预测数据失败:', error)
  } finally {
    loading.value = false

    // 确保 DOM 响应式更新（ loading 遮罩消失后）再初始化和更新图表
    await nextTick()
    updateCharts()
  }
}

// 基础下拉选项数据加载
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
  }
}

const loadDestinations = async () => {
  try {
    const res = await getDestinationCities()
    if (res.data?.code === 200) {
      destOptions.value = res.data.data.map((city: string) => ({ label: city, value: city }))

      // 增加判断：如果未选择目的地且列表元素大于1个，默认选中第二个（索引 1）
      if (!toCity.value) {
        if (destOptions.value.length > 1) {
          toCity.value = destOptions.value[1].value // 默认选中第二个
        } else if (destOptions.value.length === 1) {
          toCity.value = destOptions.value[0].value
        }
      }
    }
  } catch (e) {
    console.error('获取目的地城市失败', e)
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
  }
}

// 1. 日期格式化统一函数 (YYYY-MM-DD)
const formatDate = (time: Date) => {
  const year = time.getFullYear()
  const month = String(time.getMonth() + 1).padStart(2, '0')
  const day = String(time.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 2. 返程日期禁用逻辑：必须在 availableDates 范围内，且【严格晚于】去程日期
const disabledReturnDate = (time: Date) => {
  if (!availableDates.value || availableDates.value.length === 0) return false

  const dateStr = formatDate(time)

  // 条件 A: 不在数据可售日期范围内，禁用
  const isNotInAvailable = !availableDates.value.includes(dateStr)

  // 条件 B: 早于或等于去程日期，禁用 (dateStr <= departureDate.value)
  let isNotAfterDeparture = false
  if (departureDate.value) {
    // 字符串拼写对比 "2022-04-19" <= "2022-04-19" 为 true，即当天和之前全部禁用
    isNotAfterDeparture = dateStr <= departureDate.value
  }

  return isNotInAvailable || isNotAfterDeparture
}

// 监听去程变化：若返程日期小于等于新的去程日期，则自动清空返程日期
watch(departureDate, (newDepDate) => {
  if (returnDate.value && newDepDate && returnDate.value <= newDepDate) {
    returnDate.value = '' // 清空返程日期，提示用户重新选择
  }
})

// 动态计算返程弹窗打开时的默认面板月份：
// 优先使用已选的去程日期，若未选去程则兜底显示 2022-04-21
const defaultReturnPickerPage = computed(() => {
  if (departureDate.value) {
    return new Date(departureDate.value)
  }
  return new Date(2022, 3, 21)
})

const handleResize = () => {
  departureChart?.resize()
  returnChart?.resize()
}

// 4. 生命周期
onMounted(async () => {
  await loadOrigins()
  await loadDestinations()
  await loadDates()

  await handleSearch()

  window.addEventListener('resize', handleResize)
})
</script>

<template>
  <div
    class="predictor-container"
    v-loading="loading"
    element-loading-background="rgba(0, 0, 0, 0.5)"
    :style="{ backgroundImage: `url(${skyBg})` }"
  >
    <!-- 1. 顶栏筛选区 -->
    <div class="top-filter-navigation">
      <!-- 预测未来 n 天：用户自由输入数字 -->
      <div class="days-input-wrapper">
        <span class="prefix-label">预测未来</span>
        <el-input-number
          v-model="predictDays"
          :min="1"
          :max="180"
          :controls="false"
          class="days-number-input"
        />
        <span class="suffix-label">天机票</span>
      </div>

      <div class="inputs-row">
        <!-- 出发城市 -->
        <el-select v-model="fromCity" placeholder="出发城市" class="dark-select route-select">
          <el-option
            v-for="item in originOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>

        <!-- 切换城市图标 -->
        <el-icon class="transfer-icon" @click="swapCities"><Switch /></el-icon>

        <!-- 到达城市 -->
        <el-select v-model="toCity" placeholder="到达城市" class="dark-select route-select">
          <el-option
            v-for="item in destOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>

        <!-- 去程日期：绑定 disabledDepartureDate -->
        <el-date-picker
          v-model="departureDate"
          type="date"
          placeholder="去程日期"
          class="dark-date-picker"
          value-format="YYYY-MM-DD"
          :disabled-date="disabledDepartureDate"
        />

        <!-- 返程日期：绑定 disabledReturnDate -->
        <el-date-picker
          v-model="returnDate"
          type="date"
          placeholder="返程日期 (可选)"
          class="dark-date-picker"
          value-format="YYYY-MM-DD"
          :disabled-date="disabledReturnDate"
          :default-value="defaultReturnPickerPage"
        />

        <el-button type="primary" class="search-btn" @click="handleSearch">
          <el-icon><Search /></el-icon>查询预测
        </el-button>
      </div>
    </div>

    <!-- 2. 上方卡片：去程预测最低机票趋势 -->
    <div class="section-card">
      <div class="card-title-bar">
        <div class="step-badge">去程</div>
        <div class="title-text">{{ fromCity }} ✈ {{ toCity }} ({{ departureDate }})</div>

        <div v-if="departureBestBuy" class="best-buy-tag">
          🔥 最佳购买日期: {{ departureBestBuy.date }} (${{ departureBestBuy.price }})
        </div>

        <div v-if="departureSuggestion" class="suggestion-tag">
          💡 {{ departureSuggestion }}
        </div>
      </div>
      <div ref="departureChartRef" class="chart-canvas-body"></div>
    </div>

    <!-- 3. 下方卡片：返程预测最低机票趋势 -->
    <div class="section-card">
      <div class="card-title-bar">
        <div class="step-badge return-badge">返程</div>
        <div class="title-text">
          <template v-if="returnDate">
            {{ toCity }} ✈ {{ fromCity }} ({{ returnDate }})
          </template>
          <template v-else>
            请选择返程日期以查看返程预测
          </template>
        </div>

        <div v-if="returnBestBuy" class="best-buy-tag">
          🔥 最佳购买日期: {{ returnBestBuy.date }} (${{ returnBestBuy.price }})
        </div>

        <div v-if="returnSuggestion" class="suggestion-tag">
          💡 {{ returnSuggestion }}
        </div>
      </div>
      <div ref="returnChartRef" class="chart-canvas-body"></div>
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
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
  z-index: 10;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.top-filter-navigation {
  display: flex;
  align-items: center;
  gap: 12px;
}

.days-input-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  padding: 0 10px;
  height: 32px;
  flex-shrink: 0;
}

.prefix-label,
.suffix-label {
  font-size: 13px;
  color: #94a3b8;
  white-space: nowrap;
}

.days-number-input {
  width: 45px !important;
}

:deep(.days-number-input .el-input__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
}

:deep(.days-number-input .el-input__inner) {
  color: #38bdf8 !important;
  font-weight: bold;
  text-align: center;
}

.inputs-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.route-select {
  flex: 1;
}

.transfer-icon {
  color: #94a3b8;
  cursor: pointer;
  transition: transform 0.2s;
}

.transfer-icon:hover {
  color: #38bdf8;
  transform: rotate(180deg);
}

.dark-date-picker {
  flex: 1.2;
}

.search-btn {
  height: 32px !important;
  padding: 0 20px !important;
  flex-shrink: 0;
}

.section-card {
  background-color: rgba(19, 25, 36, 0.82);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 12px 16px;
  min-height: 0;
}

.card-title-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 8px;
  flex-shrink: 0;
}

.step-badge {
  background-color: #0284c7;
  color: #fff;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.step-badge.return-badge {
  background-color: #ec4899;
}

.title-text {
  font-size: 14px;
  font-weight: bold;
  color: #f1f5f9;
}

.best-buy-tag {
  background: rgba(245, 158, 11, 0.2);
  border: 1px solid #f59e0b;
  color: #fbbf24;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.suggestion-tag {
  margin-left: auto;
  color: #38bdf8;
  font-size: 12px;
  background: rgba(56, 189, 248, 0.1);
  padding: 2px 10px;
  border-radius: 4px;
}

.chart-canvas-body {
  width: 100%;
  flex: 1;
  min-height: 0;
}
</style>
