<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

interface Props {
  notebookId: string
  paragraphId: string
  title: string
  badgeText?: string | number
  badgeType?: 'green' | 'pink'
  // 图表/数据渲染类型: 'line' | 'bar' | 'dual-axis' | 'pie' | 'table'
  renderType?: 'line' | 'bar' | 'dual-axis' | 'pie' | 'table'
  subText?: string
  queryParams: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  badgeText: '✓',
  badgeType: 'green',
  renderType: 'bar',
  subText: ''
})

const chartRef = ref<HTMLElement | null>(null)
let myChart: echarts.ECharts | null = null
const loading = ref(false)

// 表格数据结构定义
const tableHeaders = ref<string[]>([])
const tableRows = ref<string[][]>([])

// 通用多列 TSV 数据解析器
const parseZeppelinTable = (rawText: string) => {
  if (!rawText) return null
  const lines = rawText.trim().split('\n')
  const headers = lines[0].split('\t')
  const rows = lines.slice(1).map(line => line.split('\t'))

  // 按列拆分数据（方便 ECharts 绘图）
  const columns: string[][] = headers.map((_, colIndex) => rows.map(r => r[colIndex] || ''))

  return { headers, rows, columns }
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
      if (data) {
        tableHeaders.value = data.headers
        tableRows.value = data.rows

        // 如果不是表格类型，渲染 ECharts 图表
        if (props.renderType !== 'table' && data.columns[0]?.length > 0) {
          await nextTick()
          renderChart(data)
        }
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
  const xData = columns[0]
  let option: echarts.EChartsOption = {}

  // 1. 饼图
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
  // 2. 双 Y 轴复合图 (适用于 1. 热门航线)
  else if (props.renderType === 'dual-axis') {
    const y1Data = columns[1].map(Number)
    const y2Data = columns[2] ? columns[2].map(Number) : []
    option = {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      legend: { data: [headers[1], headers[2]].filter(Boolean), textStyle: { color: '#a0aec0' } },
      grid: { top: 40, bottom: 35, left: 45, right: 45, containLabel: true },
      xAxis: {
        type: 'category',
        data: xData,
        axisLine: { lineStyle: { color: '#4a5568' } },
        axisLabel: { color: '#a0aec0', fontSize: 10, rotate: 20 }
      },
      yAxis: [
        { type: 'value', name: headers[1], axisLabel: { color: '#a0aec0' }, splitLine: { lineStyle: { color: 'rgba(74, 85, 104, 0.15)' } } },
        { type: 'value', name: headers[2] || '', axisLabel: { color: '#a0aec0' }, splitLine: { show: false } }
      ],
      series: [
        { name: headers[1], type: 'bar', data: y1Data, barWidth: '35%', itemStyle: { color: '#38bdf8', borderRadius: [2, 2, 0, 0] } },
        { name: headers[2], type: 'line', yAxisIndex: 1, data: y2Data, smooth: true, itemStyle: { color: '#ff7597' }, lineStyle: { width: 3 } }
      ]
    }
  }
  // 3. 折线图
  else if (props.renderType === 'line') {
    const y1Data = columns[1].map(Number)
    option = {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { top: 30, bottom: 30, left: 40, right: 30, containLabel: true },
      xAxis: { type: 'category', data: xData, axisLine: { lineStyle: { color: '#4a5568' } }, axisLabel: { color: '#a0aec0', rotate: 20 } },
      yAxis: { type: 'value', axisLabel: { color: '#a0aec0' }, splitLine: { lineStyle: { color: 'rgba(74, 85, 104, 0.15)' } } },
      series: [{ name: headers[1], type: 'line', smooth: true, data: y1Data, itemStyle: { color: '#ff7597' }, lineStyle: { width: 3 } }]
    }
  }
  // 4. 柱状图
  else {
    const y1Data = columns[1].map(Number)
    option = {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { top: 30, bottom: 30, left: 40, right: 30, containLabel: true },
      xAxis: { type: 'category', data: xData, axisLine: { lineStyle: { color: '#4a5568' } }, axisLabel: { color: '#a0aec0', rotate: 20, fontSize: 10 } },
      yAxis: { type: 'value', axisLabel: { color: '#a0aec0' }, splitLine: { lineStyle: { color: 'rgba(74, 85, 104, 0.15)' } } },
      series: [{ name: headers[1], type: 'bar', data: y1Data, itemStyle: { color: '#10b981', borderRadius: [2, 2, 0, 0] } }]
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
    <!-- 头部 Title 栏 -->
    <div class="card-title-bar" :class="{ 'has-step-badge': badgeType === 'pink' }">
      <div :class="badgeType === 'green' ? 'status-badge-green' : 'step-badge-pink'">{{ badgeText }}</div>
      <div class="title-text">{{ title }}</div>
      <div v-if="loading" class="loading-hint">计算中...</div>
    </div>

    <div v-if="subText" class="sub-hint-text">{{ subText }}</div>

    <!-- 视图渲染区 A: 数据表格 (适用于 2.1 跳水榜, 2.2 暴涨榜, 3. 临期余票) -->
    <div v-if="renderType === 'table'" class="table-container">
      <table v-if="tableRows.length > 0" class="custom-table">
        <thead>
          <tr>
            <th v-for="(h, i) in tableHeaders" :key="i">{{ h }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rIdx) in tableRows" :key="rIdx">
            <td v-for="(cell, cIdx) in row" :key="cIdx" :class="{
              'highlight-green': cell.includes('抄底') || cell.includes('-'),
              'highlight-pink': cell.includes('暴涨') || cell.includes('观望') || cell.includes('订票')
            }">
              {{ cell }}
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else-if="!loading" class="no-data-hint">暂无符合条件的数据</div>
    </div>

    <!-- 视图渲染区 B: ECharts 画布 -->
    <div v-else ref="chartRef" class="chart-canvas-body"></div>
  </div>
</template>

<style scoped>
.section-card {
  background-color: rgba(19, 25, 36, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.card-title-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(51, 65, 85, 0.3);
  padding: 10px 16px;
  flex-shrink: 0;
  color: #fff;
}
.card-title-bar.has-step-badge {
  padding: 0 16px 0 0;
  height: 40px;
  border-bottom: none;
  background-color: rgba(24, 34, 50, 0.9);
}

.status-badge-green,
.step-badge-pink {
  width: 40px !important;
  height: 40px !important;
  min-width: 40px !important;
  max-width: 40px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 15px !important;
  font-weight: 900 !important;
  color: #ffffff !important;
  margin-right: 12px !important;
  flex-shrink: 0 !important;
  border-radius: 0 !important;
}

.status-badge-green {
  background-color: #10b981 !important;
}

.step-badge-pink {
  background-color: #ff7597 !important;
}

.card-title-bar {
  display: flex;
  align-items: center;
  height: 40px;
  padding: 0 16px 0 0 !important;
  background-color: rgba(24, 34, 50, 0.9);
  border-bottom: none;
  color: #fff;
}

.title-text { font-size: 13px; font-weight: bold; }
.loading-hint { font-size: 12px; color: #38bdf8; margin-left: auto; }
.sub-hint-text { color: #64748b; font-size: 11px; padding: 6px 16px 0 16px; flex-shrink: 0; }

.chart-canvas-body { width: 100%; flex: 1; min-height: 0; }

.table-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px 16px;
}
.custom-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  text-align: left;
}
.custom-table th {
  position: sticky;
  top: 0;
  background-color: rgba(30, 41, 59, 0.95);
  color: #94a3b8;
  padding: 8px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.custom-table td {
  padding: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: #cbd5e1;
}
.custom-table tr:hover td {
  background-color: rgba(255, 255, 255, 0.03);
}

.highlight-green { color: #34d399 !important; font-weight: bold; }
.highlight-pink { color: #f472b6 !important; font-weight: bold; }

.no-data-hint {
  text-align: center; color: #64748b; font-size: 12px; margin-top: 20px;
}

.table-container::-webkit-scrollbar { width: 4px; }
.table-container::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: 2px; }
</style>
