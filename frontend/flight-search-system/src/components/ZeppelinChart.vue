<!-- src/components/ZeppelinChart.vue -->
<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

interface Props {
  notebookId: string
  paragraphId: string
  title: string
  badgeText?: string | number
  badgeType?: 'green' | 'pink'
  // 图表渲染类型: 'line'(折线/双折线) | 'bar'(柱状) | 'dual-axis'(双Y轴复合图) | 'pie'(饼图)
  renderType?: 'line' | 'bar' | 'dual-axis' | 'pie'
  subText?: string
  queryParams: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  badgeText: '✓',
  badgeType: 'green',
  renderType: 'line',
  subText: ''
})

const chartRef = ref<HTMLElement | null>(null)
let myChart: echarts.ECharts | null = null
const loading = ref(false)

// 通用多列 TSV 数据解析器
const parseZeppelinTable = (rawText: string) => {
  if (!rawText) return null
  const lines = rawText.trim().split('\n')
  const headers = lines[0].split('\t')
  const rows = lines.slice(1).map(line => line.split('\t'))

  // 按列拆分数据
  const columns: string[][] = headers.map((_, colIndex) => rows.map(r => r[colIndex] || ''))

  return { headers, columns }
}

// 加载 Zeppelin 数据
const fetchData = async () => {
  if (!props.notebookId || !props.paragraphId) return
  loading.value = true
  try {
    const res = await axios.post(`/api/notebook/run/${props.notebookId}/${props.paragraphId}`, {
      params: props.queryParams
    })
    const body = res.data?.body || {}
    const msgItem = body.msg?.[0]
    const rawText = (typeof msgItem === 'object' && msgItem !== null) ? msgItem.data : msgItem

    if (rawText && typeof rawText === 'string') {
      const data = parseZeppelinTable(rawText)
      if (data && data.columns[0]?.length > 0) {
        renderChart(data)
      }
    }
  } catch (err) {
    console.error(`[${props.title}] 加载失败:`, err)
  } finally {
    loading.value = false
  }
}

// 构建不同类型图表的 ECharts Option
const renderChart = (data: { headers: string[]; columns: string[][] }) => {
  if (!chartRef.value) return
  if (!myChart) myChart = echarts.init(chartRef.value)

  const { headers, columns } = data
  const xData = columns[0] // 第 0 列通常是 X 轴/类别名称
  let option: echarts.EChartsOption = {}

  // 1. 饼图 / 环形图 (适用于 Paragraph 4)
  if (props.renderType === 'pie') {
    const pieData = xData.map((name, i) => ({
      name,
      value: Number(columns[1][i]) || 0
    }))
    option = {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', right: '5%', top: 'center', textStyle: { color: '#a0aec0', fontSize: 11 } },
      series: [{
        name: headers[1] || '占比',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 4, borderColor: '#131924', borderWidth: 2 },
        label: { show: false },
        data: pieData
      }]
    }
  }
  // 2. 双 Y 轴复合图 (适用于 Paragraph 3 和 Paragraph 5)
  else if (props.renderType === 'dual-axis') {
    const y1Data = columns[1].map(Number)
    const y2Data = columns[2].map(Number)
    option = {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      legend: { data: [headers[1], headers[2]], textStyle: { color: '#a0aec0' } },
      grid: { top: 40, bottom: 30, left: 40, right: 40, containLabel: true },
      xAxis: { type: 'category', data: xData, axisLine: { lineStyle: { color: '#4a5568' } }, axisLabel: { color: '#a0aec0', fontSize: 10 } },
      yAxis: [
        { type: 'value', name: headers[1], axisLabel: { color: '#a0aec0' }, splitLine: { lineStyle: { color: 'rgba(74, 85, 104, 0.15)' } } },
        { type: 'value', name: headers[2], axisLabel: { color: '#a0aec0' }, splitLine: { show: false } }
      ],
      series: [
        { name: headers[1], type: 'bar', data: y1Data, barWidth: '40%', itemStyle: { color: '#38bdf8', borderRadius: [2, 2, 0, 0] } },
        { name: headers[2], type: 'line', yAxisIndex: 1, data: y2Data, smooth: true, itemStyle: { color: '#ff7597' }, lineStyle: { width: 3 } }
      ]
    }
  }
  // 3. 多线折线图 / 双折线图 (适用于 Paragraph 1)
  else if (props.renderType === 'line') {
    const y1Data = columns[1].map(Number)
    const y2Data = columns[2] ? columns[2].map(Number) : []

    const seriesList: any[] = [
      { name: headers[1], type: 'line', smooth: true, data: y1Data, itemStyle: { color: '#ff7597' }, lineStyle: { width: 3 } }
    ]
    if (headers[2] && y2Data.length) {
      seriesList.push({ name: headers[2], type: 'line', smooth: true, data: y2Data, itemStyle: { color: '#38bdf8' }, lineStyle: { width: 3 } })
    }

    option = {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      legend: { data: headers.slice(1, 3), textStyle: { color: '#a0aec0' } },
      grid: { top: 40, bottom: 30, left: 40, right: 40, containLabel: true },
      xAxis: { type: 'category', data: xData, axisLine: { lineStyle: { color: '#4a5568' } }, axisLabel: { color: '#a0aec0' } },
      yAxis: { type: 'value', axisLabel: { color: '#a0aec0', formatter: (v: number) => `¥${v}` }, splitLine: { lineStyle: { color: 'rgba(74, 85, 104, 0.15)' } } },
      series: seriesList
    }
  }
  // 4. 多柱/单柱图 (适用于 Paragraph 2)
  else {
    const y1Data = columns[1].map(Number)
    const y2Data = columns[2] ? columns[2].map(Number) : []

    const seriesList: any[] = [
      { name: headers[1], type: 'bar', data: y1Data, itemStyle: { color: '#f59e0b', borderRadius: [2, 2, 0, 0] } }
    ]
    if (headers[2] && y2Data.length) {
      seriesList.push({ name: headers[2], type: 'bar', data: y2Data, itemStyle: { color: '#10b981', borderRadius: [2, 2, 0, 0] } })
    }

    option = {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      legend: { data: headers.slice(1, 3), textStyle: { color: '#a0aec0' } },
      grid: { top: 40, bottom: 30, left: 40, right: 40, containLabel: true },
      xAxis: { type: 'category', data: xData, axisLine: { lineStyle: { color: '#4a5568' } }, axisLabel: { color: '#a0aec0', rotate: 25, fontSize: 10 } },
      yAxis: { type: 'value', axisLabel: { color: '#a0aec0', formatter: (v: number) => `¥${v}` }, splitLine: { lineStyle: { color: 'rgba(74, 85, 104, 0.15)' } } },
      series: seriesList
    }
  }

  myChart.setOption(option)
}

watch(() => props.queryParams, () => fetchData(), { deep: true })
const handleResize = () => myChart?.resize()

onMounted(() => {
  fetchData()
  window.addEventListener('resize', handleResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  myChart?.dispose()
})
</script>

<template>
  <div class="section-card">
    <div class="card-title-bar" :class="{ 'has-step-badge': badgeType === 'pink' }">
      <div :class="badgeType === 'green' ? 'status-badge-green' : 'step-badge-pink'">{{ badgeText }}</div>
      <div class="title-text">{{ title }}</div>
      <div v-if="loading" class="loading-hint">计算中...</div>
    </div>
    <div v-if="subText" class="sub-hint-text">{{ subText }}</div>
    <div ref="chartRef" class="chart-canvas-body"></div>
  </div>
</template>

<style scoped>
.section-card {
  background-color: rgba(19, 25, 36, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  display: flex; flex-direction: column;
  width: 100%; height: 100%; box-sizing: border-box; overflow: hidden;
}
.card-title-bar {
  display: flex; align-items: center; gap: 10px;
  border-bottom: 1px solid rgba(51, 65, 85, 0.3); padding: 10px 16px; flex-shrink: 0; color: #fff;
}
.card-title-bar.has-step-badge {
  padding: 0 16px 0 0; height: 40px; border-bottom: none; background-color: rgba(24, 34, 50, 0.9);
}
.status-badge-green {
  background-color: #10b981; color: #fff; width: 18px; height: 18px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 11px;
}
.step-badge-pink {
  background-color: #ff7597; color: #fff; width: 40px; height: 100%;
  display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 900; margin-right: 10px;
}
.title-text { font-size: 13px; font-weight: bold; }
.loading-hint { font-size: 12px; color: #38bdf8; margin-left: auto; }
.sub-hint-text { text-align: center; color: #64748b; font-size: 11px; margin-top: 6px; flex-shrink: 0; }
.chart-canvas-body { width: 100%; flex: 1; min-height: 0; }
</style>

