<!-- src/views/PredictorDashboard.vue -->
<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Search, Switch } from '@element-plus/icons-vue'
import ZeppelinChart from '@/components/ZeppelinChart.vue'
import skyBg from '../pictures/天空.jpg'

// Notebook ID
const NOTEBOOK_ID = '2MZABZFK3'

// 填入你 5 个段落对应的真实 Paragraph ID
const PARAGRAPH_IDS = {
  p1_routeTrend: 'paragraph_1784631594952_753660793', // Paragraph 1: 指定航线价格趋势 (折线图)
  p2_destRank: 'paragraph_1620000000000_222222222',   // Paragraph 2: 最低价目的地排行榜 (柱状图)
  p3_offerRank: 'paragraph_1620000000000_333333333',  // Paragraph 3: 热门航线报价热度与价格变动 (双Y轴图)
  p4_sharePie: 'paragraph_1620000000000_444444444',   // Paragraph 4: 航司报价供给占比 (环形饼图)
  p5_shareVsPrice: 'paragraph_1620000000000_555555555'// Paragraph 5: 航司供给占比 vs 均价 (双Y轴图)
}

// 选项卡（分区）定义
const tabOptions = [
  { label: '航线价格与趋势分析', value: 'p1' },
  { label: '低价目的地 TOP 15 推荐', value: 'p2' },
  { label: '热门航线报价热度与价格变动', value: 'p3' },
  { label: '各航司报价供给占比分布', value: 'p4' },
  { label: '航司报价供给占比 vs 平均含税报价', value: 'p5' }
]

// 当前选中的分析分区（默认展示第一个）
const activeTab = ref('p1')

// 机场选项
const cityOptions = ref([
  { label: '广州 (CAN)', value: 'CAN' },
  { label: '曼谷 (BKK)', value: 'BKK' },
  { label: '纽约 (LGA)', value: 'LGA' },
  { label: '旧金山 (SFO)', value: 'SFO' }
])

// 顶栏筛选状态
const fromCity = ref('CAN')
const toCity = ref('BKK')
const departureDate = ref('2022-04-18')

// 发送给 Zeppelin 的响应式参数
const activeQueryParams = reactive({
  '搜索日期': departureDate.value,
  '起点机场': fromCity.value,
  '终点机场': toCity.value
})

// 点击“查询”统一刷新数据
const handleSearch = () => {
  activeQueryParams['搜索日期'] = departureDate.value
  activeQueryParams['起点机场'] = fromCity.value
  activeQueryParams['终点机场'] = toCity.value
}

// 切换起点与终点
const swapCities = () => {
  const temp = fromCity.value
  fromCity.value = toCity.value
  toCity.value = temp
}
</script>

<template>
  <div class="predictor-container" :style="{ backgroundImage: `url(${skyBg})` }">

    <!-- 1. 顶部筛选控制栏 -->
    <div class="top-filter-navigation">
      <div class="icon-clock-box">📊</div>

      <!-- 左侧：线路与日期筛选器 -->
      <div class="inputs-row">
        <el-select v-model="fromCity" placeholder="起点机场" class="dark-select route-select">
          <el-option v-for="item in cityOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>

        <el-icon class="transfer-icon" @click="swapCities" style="cursor: pointer; color: #38bdf8;"><Switch /></el-icon>

        <el-select v-model="toCity" placeholder="终点机场" class="dark-select route-select">
          <el-option v-for="item in cityOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>

        <el-date-picker
          v-model="departureDate"
          type="date"
          placeholder="选择搜索日期"
          class="dark-date-picker"
          value-format="YYYY-MM-DD"
        />

        <el-button type="primary" class="search-btn" @click="handleSearch">
          <el-icon><Search /></el-icon>数据检索 / 刷新
        </el-button>
      </div>

      <!-- 空白占位拉开距离 -->
      <div class="flex-spacer"></div>

      <!-- 右上角：分析分区选择列表 -->
      <div class="view-selector-box">
        <span class="selector-label">选择视图：</span>
        <el-select v-model="activeTab" class="dark-select tab-select" placeholder="切换分析分区">
          <el-option
            v-for="item in tabOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </div>
    </div>

    <!-- 2. 看板核心区 (按需要选择只展示选中的单视图) -->
    <div class="single-chart-display-layout">

      <!-- 分区 1：指定航线价格趋势分析 -->
      <div v-if="activeTab === 'p1'" class="chart-wrapper">
        <ZeppelinChart
          :notebook-id="NOTEBOOK_ID"
          :paragraph-id="PARAGRAPH_IDS.p1_routeTrend"
          :title="`航线价格与趋势分析 (${fromCity} ➔ ${toCity})`"
          badge-text="01" badge-type="green"
          render-type="line"
          sub-text="观察目标航线随着未来出发日期的最低价与均价波动"
          :query-params="activeQueryParams"
        />
      </div>

      <!-- 分区 2：低价目的地排行榜 -->
      <div v-if="activeTab === 'p2'" class="chart-wrapper">
        <ZeppelinChart
          :notebook-id="NOTEBOOK_ID"
          :paragraph-id="PARAGRAPH_IDS.p2_destRank"
          title="低价目的地 TOP 15 推荐"
          badge-text="02" badge-type="green"
          render-type="bar"
          sub-text="对比全网最低价与均价，挑选最便宜目的地"
          :query-params="activeQueryParams"
        />
      </div>

      <!-- 分区 3：热门航线报价热度 -->
      <div v-if="activeTab === 'p3'" class="chart-wrapper">
        <ZeppelinChart
          :notebook-id="NOTEBOOK_ID"
          :paragraph-id="PARAGRAPH_IDS.p3_offerRank"
          title="TOP 10 热门航线报价热度与价格变动"
          badge-text="03" badge-type="green"
          render-type="dual-axis"
          sub-text="柱状：报价快照数 (左轴) | 折线：均价变化率% (右轴)"
          :query-params="activeQueryParams"
        />
      </div>

      <!-- 分区 4：各航司报价供给占比 -->
      <div v-if="activeTab === 'p4'" class="chart-wrapper">
        <ZeppelinChart
          :notebook-id="NOTEBOOK_ID"
          :paragraph-id="PARAGRAPH_IDS.p4_sharePie"
          title="各航司报价供给占比分布"
          badge-text="04" badge-type="green"
          render-type="pie"
          sub-text="直观呈现市场中各航司的运力/报价投放主力"
          :query-params="activeQueryParams"
        />
      </div>

      <!-- 分区 5：航司报价供给占比 vs 平均含税报价 -->
      <div v-if="activeTab === 'p5'" class="chart-wrapper">
        <ZeppelinChart
          :notebook-id="NOTEBOOK_ID"
          :paragraph-id="PARAGRAPH_IDS.p5_shareVsPrice"
          title="航司报价供给占比 vs 平均含税报价"
          badge-text="05" badge-type="green"
          render-type="dual-axis"
          sub-text="柱状：供给占比% (左轴) | 折线：平均报价USD (右轴)"
          :query-params="activeQueryParams"
        />
      </div>

    </div>
  </div>
</template>

<style scoped>
/* 页面基本布局 */
.predictor-container {
  position: fixed;
  top: 0; bottom: 0; right: 0; left: 240px;
  height: 100vh !important;
  box-sizing: border-box;
  padding: 20px;
  display: flex; flex-direction: column; gap: 16px;
  overflow: hidden; /* 单图模式下取消整体页面滚动 */
  z-index: 10;
  background-size: cover; background-position: center;
}

.top-filter-navigation {
  display: flex; align-items: center; gap: 16px; flex-shrink: 0;
  width: 100%;
}
.icon-clock-box { font-size: 18px; color: #9ca3af; flex-shrink: 0; }
.inputs-row { display: flex; align-items: center; gap: 12px; }
.route-select { width: 140px; }
.dark-date-picker { width: 180px; }

.flex-spacer { flex: 1; } /* 挤开左右内容 */

/* 右上角下拉选择框 */
.view-selector-box {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.selector-label {
  color: #9ca3af;
  font-size: 13px;
  white-space: nowrap;
}
.tab-select {
  width: 260px;
}

/* 强制将日期选择器背景改为白色，文字保持清晰 */
:deep(.light-date-picker),
:deep(.light-date-picker .el-input__wrapper) {
  background-color: #ffffff !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  border: 1px solid #cbd5e1 !important;
}

/* 调整内部文字与图标颜色 */
:deep(.light-date-picker .el-input__inner) {
  color: #0284c7 !important;
  font-weight: 700 !important;
  font-size: 14px !important;
}

:deep(.light-date-picker .el-input__prefix),
:deep(.light-date-picker .el-input__suffix) {
  color: #64748b !important;
}

.search-btn { height: 32px !important; padding: 0 16px !important; font-weight: 600; }

/* 单个图表占满展示区域 */
.single-chart-display-layout {
  flex: 1;
  width: 100%;
  height: calc(100% - 50px);
  position: relative;
}

.chart-wrapper {
  width: 100%;
  height: 100%;
}
</style>
