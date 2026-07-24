<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import ZeppelinChart from '@/components/ZeppelinChart.vue'
import skyBg from '../pictures/天空.jpg'

// 1. Notebook & Paragraph 配置
const NOTEBOOK_ID = '2MZABZFK3' // Notebook ID
const PARAGRAPH_IDS = {
  popularRoute: 'paragraph_1784707702638_1511698672', // 1.1 热门航线 TOP 15
  priceDrop: 'paragraph_1784865972906_441817053',    // 2.1 价格跳水榜
  priceSurge: 'paragraph_1784866678648_1702634311',   // 2.2 价格暴涨预警榜
  urgentFlight: 'paragraph_1784883095841_504737919'   // 3.1 临期余票告急
}

// 2. 当前选中的视图模式
const activeTab = ref<'popular' | 'trends' | 'urgent'>('popular')

// 3. 全局筛选条件
const searchForm = reactive({
  searchDate: '2022-04-18',
  originCity: 'New York',
  maxSeats: 5,
  sortType: 'seats_asc' // 默认
})

// 3 种排序选项
const sortOptions = [
  { label: '剩余座位数 (从低到高)', value: 'seats_asc' },
  { label: '距起飞天数 (从低到高)', value: 'days_asc' },
  { label: '机票价格 (从低到高)', value: 'price_asc' }
]

// 筛选下拉框可选项
const dateOptions = ['2022-04-18', '2022-04-19', '2022-04-22', '2022-04-23', '2022-04-26', '2022-04-27']
const cityOptions = [
  'Atlanta', 'Boston', 'Charlotte', 'Chicago', 'Dallas-Fort Worth',
  'Denver', 'Detroit', 'Dulles', 'Los Angeles', 'Miami',
  'New York', 'Newark', 'Oakland', 'Philadelphia', 'San Francisco'
]

// 动态构建 queryParams
const chartQueryParams = computed(() => {
  return {
    '搜索日期': String(searchForm.searchDate),
    '出发城市': String(searchForm.originCity),
    '最大剩余座位': String(searchForm.maxSeats),
    '排序方式': String(searchForm.sortType)
  }
})
</script>

<template>
  <div class="dashboard-container" :style="{ backgroundImage: `url(${skyBg})` }">
    <!-- 顶栏：标题 + 筛选器 + 3大板块 Tab 切换 -->
    <header class="dashboard-header">
      <div class="header-title">
        <span class="pulse-icon"></span>
        <h2>航班决策看板</h2>
      </div>

      <!-- 全局筛选控制栏 -->
      <div class="filter-bar">
        <div class="filter-item">
          <label>搜索日期：</label>
          <el-select v-model="searchForm.searchDate" size="small" class="custom-select">
            <el-option v-for="d in dateOptions" :key="d" :label="d" :value="d" />
          </el-select>
        </div>

        <div class="filter-item">
          <label>出发城市：</label>
          <el-select v-model="searchForm.originCity" size="small" class="custom-select">
            <el-option v-for="c in cityOptions" :key="c" :label="c" :value="c" />
          </el-select>
        </div>

        <div class="filter-item">
          <label>临期最大余票：</label>
          <el-input-number
            v-model="searchForm.maxSeats"
            :min="1"
            :max="10"
            size="small"
            controls-position="right"
            class="custom-input-number"
          />
        </div>
        <div v-if="activeTab === 'urgent'" class="filter-item">
            <label>排序方式：</label>
            <el-select v-model="searchForm.sortType" size="small" class="custom-select" style="width: 170px;">
              <el-option v-for="s in sortOptions" :key="s.value" :label="s.label" :value="s.value" />
            </el-select>
          </div>
        </div>

      <!-- 3 大板块 Tab 切换按钮 -->
      <div class="view-tabs">
        <button :class="{ active: activeTab === 'popular' }" @click="activeTab = 'popular'">热门航线 Top15</button>
        <button :class="{ active: activeTab === 'trends' }" @click="activeTab = 'trends'">票价波动榜 (跳水/暴涨)</button>
        <button :class="{ active: activeTab === 'urgent' }" @click="activeTab = 'urgent'">临期余票告急</button>
      </div>
    </header>

    <!-- 主体图表展示区域 -->
    <main class="dashboard-body">

      <!-- 看板 1: 热门航线 TOP 15 -->
      <div v-if="activeTab === 'popular'" class="single-view">
        <ZeppelinChart
          :notebook-id="NOTEBOOK_ID"
          :paragraph-id="PARAGRAPH_IDS.popularRoute"
          title="热门航线热度排行榜 (TOP 15)"
          badge-text="1"
          badge-type="green"
          render-type="dual-axis"
          sub-text="柱状: 报价搜寻数 (热度) | 折线: 航线均价"
          :query-params="chartQueryParams"
        />
      </div>

      <!-- 看板 2: 行情波动（跳水榜 vs 暴涨榜）同页左右对比视图  -->
      <div v-else-if="activeTab === 'trends'" class="trends-split-box">
        <div class="split-card">
          <ZeppelinChart
            :notebook-id="NOTEBOOK_ID"
            :paragraph-id="PARAGRAPH_IDS.priceDrop"
            title="今日价格跳水榜"
            badge-text="跌"
            badge-type="green"
            render-type="table"
            sub-text="跌幅最大的航线 (抄底推荐)"
            :query-params="chartQueryParams"
          />
        </div>
        <div class="split-card">
          <ZeppelinChart
            :notebook-id="NOTEBOOK_ID"
            :paragraph-id="PARAGRAPH_IDS.priceSurge"
            title="价格暴涨预警榜"
            badge-text="涨"
            badge-type="pink"
            render-type="table"
            sub-text="涨幅最大的航线 (及早订票)"
            :query-params="chartQueryParams"
          />
        </div>
      </div>

      <!-- 看板 3: 临期余票告急低价榜  -->
      <div v-else-if="activeTab === 'urgent'" class="single-view">
        <ZeppelinChart
          :notebook-id="NOTEBOOK_ID"
          :paragraph-id="PARAGRAPH_IDS.urgentFlight"
          title="临期（7天内）余票告急低价机票"
          badge-text="3"
          badge-type="green"
          render-type="table"
          sub-text="优先呈现余票 1~5 张且价格较低的舱位"
          :query-params="chartQueryParams"
        />
      </div>

    </main>
  </div>
</template>

<style scoped>
.dashboard-container {
  width: 100% !important;
  height: 100% !important;
  background-color: #0b0f19;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  color: #f1f5f9;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

.dashboard-header {
  width: 100%;
  height: 56px;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
  box-sizing: border-box;
  z-index: 10;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-title h2 {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
  background: linear-gradient(90deg, #38bdf8, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
}
.pulse-icon {
  width: 8px;
  height: 8px;
  background-color: #10b981;
  border-radius: 50%;
  box-shadow: 0 0 8px #10b981;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
}
.filter-item {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #94a3b8;
}
.custom-select {
  width: 120px;
}
.custom-input-number {
  width: 90px;
}

.view-tabs {
  display: flex;
  background: rgba(30, 41, 59, 0.6);
  padding: 3px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}
.view-tabs button {
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 5px 12px;
  font-size: 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
}
.view-tabs button.active {
  background: #38bdf8;
  color: #0f172a;
  font-weight: bold;
}

.dashboard-body {
  flex: 1;
  width: 100% !important;
  padding: 12px;
  min-height: 0;
  box-sizing: border-box;
}

.trends-split-box {
  display: flex;
  gap: 12px;
  width: 100% !important;
  height: 100%;
  box-sizing: border-box;
}

.split-card {
  flex: 1 1 0% !important;
  width: 0 !important;
  min-width: 0 !important;
  height: 100%;
}

.single-view {
  width: 100% !important;
  height: 100%;
  box-sizing: border-box;
}
</style>
