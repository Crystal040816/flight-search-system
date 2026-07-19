<script setup lang="ts">
import { ref } from 'vue'
import {
  Switch, Search, Operation, Refresh,
  SuccessFilled, Promotion, Clock, CaretTop, CaretBottom
} from '@element-plus/icons-vue'

// 引入存放图片的相对路径
import skyBg from '../pictures/天空.jpg'

// --- 顶部搜索表单状态 ---
const tripType = ref('往返')
const passengers = ref('1人, 经济舱')
const fromCity = ref('伦敦 (LON)')
const toCity = ref('纽约 (NYC)')
const dateRange = ref(['2026-08-12', '2026-08-20'])

// --- 模式切换 (自由搭配 / 航班组合) ---
const currentMode = ref('free')

// --- 筛选与排序状态 ---
const isNonStopOnly = ref(false)
const selectedStop = ref('')
const selectedAirport = ref('')
const selectedTime = ref('')
const selectedAirline = ref('')
const sortBy = ref('price')

// --- 模拟航班数据集 ---
const flightList = ref([
  {
    id: 1,
    isLowest: true,
    airline: '维珍航空',
    flightNo: 'VS45',
    aircraft: '789',
    depTime: '14:05',
    arrTime: '16:45',
    depAirport: '希思罗机场 T3',
    arrAirport: '纽约肯尼迪机场 T4',
    duration: '7h 40m',
    price: 4483,
    score: 10
  },
  {
    id: 2,
    isLowest: true,
    airline: '维珍航空',
    flightNo: 'VS3',
    aircraft: '351',
    depTime: '09:05',
    arrTime: '11:55',
    depAirport: '希思罗机场 T3',
    arrAirport: '纽约肯尼迪机场 T4',
    duration: '7h 50m',
    price: 4483,
    score: 10
  },
  {
    id: 3,
    isLowest: true,
    airline: '维珍航空',
    flightNo: 'VS25',
    aircraft: '351',
    depTime: '20:15',
    arrTime: '23:10',
    depAirport: '希思罗机场 T3',
    arrAirport: '纽约肯尼迪机场 T4',
    duration: '7h 55m',
    price: 4483,
    score: 10
  }
])

const handleSearch = () => {
  console.log('执行搜索:', fromCity.value, toCity.value, dateRange.value)
}

const handleSelect = (flightId: number) => {
  alert(`已选择去程航班 ID: ${flightId}`)
}
</script>

<template>
  <!-- 纵向外壳：确保黑条在顶部铺满，剩余部分再作为天空和内容容器 -->
  <div class="page-wrapper-non-scrollable" :style="{ backgroundImage: `url(${skyBg})` }">

    <!-- ==================== 1. 顶部黑色核心搜索栏：左右无缝铺满，上下压窄 ==================== -->
    <div class="search-sticky-bar">
      <el-select v-model="tripType" class="dark-select mini-width">
        <el-option label="往返" value="往返" />
        <el-option label="单程" value="单程" />
      </el-select>

      <el-select v-model="passengers" class="dark-select medium-width">
        <el-option label="1人, 经济舱" value="1人, 经济舱" />
        <el-option label="2人, 经济舱" value="2人, 经济舱" />
      </el-select>

      <div class="route-input-group">
        <el-input v-model="fromCity" placeholder="出发城市" class="dark-input" />
        <el-icon class="transfer-icon"><Switch /></el-icon>
        <el-input v-model="toCity" placeholder="到达城市" class="dark-input" />
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

      <span class="range-tip">前后3天</span>

      <el-button type="primary" class="search-btn" @click="handleSearch">
        <el-icon><Search /></el-icon>查询
      </el-button>
    </div>

    <!-- ==================== 2. 下部独立包装居中层：控制机票内容居中对齐 ==================== -->
    <div class="main-content-centered-layer">
      <div class="flight-search-container">

        <!-- 顶部吸顶区域（包含切换卡片、蓝色指示条、白底筛选区、黑底排序栏） -->
        <div class="sticky-fixed-header">

          <!-- 自由搭配 / 航班组合 模式切换卡片 -->
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

          <!-- 当前航程高亮信息蓝色指示条 -->
          <div class="current-route-info-bar">
            <div class="info-left">
              <span class="route-txt">{{ fromCity }} ✈ {{ toCity }}</span>
              <span class="date-txt">8月12日, 周三</span>
            </div>
            <div class="info-right-badge">返程</div>
          </div>

          <!-- 白底高级过滤筛选区 -->
          <div class="filter-panel">
            <div class="filter-row">
              <el-checkbox v-model="isNonStopOnly" class="custom-checkbox">
                直飞 <span class="sub-price">¥ 4,483.00</span>
              </el-checkbox>
              <el-select v-model="selectedStop" placeholder="中转次数" class="light-select">
                <el-option label="直飞" value="0" />
                <el-option label="中转1次" value="1" />
              </el-select>
              <el-select v-model="selectedAirport" placeholder="机场" class="light-select">
                <el-option label="希思罗机场" value="LHR" />
                <el-option label="肯尼迪机场" value="JFK" />
              </el-select>
              <el-select v-model="selectedTime" placeholder="起飞/到达时间" class="light-select">
                <el-option label="上午 (06:00-12:00)" value="morning" />
                <el-option label="下午 (12:00-18:00)" value="afternoon" />
              </el-select>
              <el-select v-model="selectedAirline" placeholder="航司联盟/航空公司" class="light-select">
                <el-option label="维珍航空" value="VS" />
              </el-select>
            </div>
          </div>

          <!-- 黑底多维排序控制栏 -->
          <div class="sort-navbar">
            <div class="sort-item" :class="{ active: sortBy === 'price' }" @click="sortBy = 'price'">价格</div>
            <div class="sort-item" :class="{ active: sortBy === 'duration' }" @click="sortBy = 'duration'">飞行时长</div>
            <div class="sort-item" :class="{ active: sortBy === 'depTime' }" @click="sortBy = 'depTime'">起飞时间</div>
            <div class="sort-item" :class="{ active: sortBy === 'arrTime' }" @click="sortBy = 'arrTime'">到达时间</div>
            <div class="sort-item" :class="{ active: sortBy === 'ratio' }" @click="sortBy = 'ratio'">性价比</div>
            <div class="plane-decoration-icon">✈</div>
          </div>
        </div>

        <!-- 下部机票列表独立滚动区 -->
        <div class="scrollable-flight-list-area">
          <div class="flight-list-wrapper">
            <div v-for="flight in flightList" :key="flight.id" class="flight-card">

              <!-- 卡片顶部基础信息与评分 -->
              <div class="card-header">
                <div class="header-left">
                  <span v-if="flight.isLowest" class="lowest-tag">当日最低价</span>
                  <span class="flight-meta">{{ flight.airline }} {{ flight.flightNo }}，机型: {{ flight.aircraft }}</span>
                </div>
                <div class="header-right-score">
                  <el-icon class="thumb-icon"><SuccessFilled /></el-icon>
                  <span>{{ flight.score }}</span>
                </div>
              </div>

              <!-- 卡片主体航程渲染 -->
              <div class="card-body">
                <div class="airline-info-layout">
                  <div class="airline-logo-placeholder">
                    <el-icon class="airline-plane-icon"><Promotion /></el-icon>
                  </div>

                  <div class="time-block departure">
                    <div class="time-node"><span class="arrow-up">⤻</span>{{ flight.depTime }}</div>
                    <div class="airport-node">{{ flight.depAirport }}</div>
                  </div>
                </div>

                <div class="route-line-center">
                  <div class="line-bar"></div>
                </div>

                <div class="time-block arrival">
                  <div class="time-node"><span class="arrow-down">⤺</span>{{ flight.arrTime }}</div>
                  <div class="airport-node">{{ flight.arrAirport }}</div>
                </div>

                <div class="duration-block">
                  <el-icon class="clock-icon"><Clock /></el-icon>
                  <span>{{ flight.duration }}</span>
                </div>
              </div>

              <!-- 卡片底部动作栏与精细价格展示 -->
              <div class="card-footer">
                <el-button size="small" class="detail-btn">航程详情</el-button>

                <div class="price-action-area">
                  <div class="price-box">
                    <span class="currency">¥</span>
                    <span class="amount">{{ flight.price.toLocaleString() }}</span>
                    <span class="tax-note">含税总价</span>
                  </div>
                  <el-button type="warning" class="select-btn" @click="handleSelect(flight.id)">选择去程</el-button>
                </div>
              </div>

            </div>
          </div>
        </div>

      </div> <!-- 结束 flight-search-container -->
    </div> <!-- 结束 main-content-centered-layer -->
  </div> <!-- 结束 page-wrapper-non-scrollable -->
</template>

<style scoped>
/* ==================== 1. 大外壳：改用纵向 Flex 布局 ==================== */
.page-wrapper-non-scrollable {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 240px;     /* 缩进左侧导航栏 */
  right: 0;
  overflow: hidden;
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  box-sizing: border-box;

  /* 核心修复：上下纵向排列 */
  display: flex;
  flex-direction: column;
}

/* ==================== 2. 顶部黑色核心搜索栏：左右彻底撑满，上下大幅压缩 ==================== */
.search-sticky-bar {
  width: 100% !important;
  background-color: #0c121c;
  padding: 0 24px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-sizing: border-box;
  flex-shrink: 0;
  border-bottom: 1px solid #1e293b;
  z-index: 99;
}

/* 输入控件矮化压缩配套样式 */
.search-sticky-bar :deep(.el-input__wrapper) {
  height: 32px !important;
}
.search-btn {
  height: 32px !important;
  line-height: 32px !important;
  padding: 0 20px !important;
}

/* ==================== 3. 下部专属居中隔离层 ==================== */
.main-content-centered-layer {
  flex: 1;
  width: 100%;
  height: 0;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  overflow: hidden;
}

/* ==================== 4. 机票主容器：稳居正中 ==================== */
.flight-search-container {
  width: 1150px;
  max-width: calc(100% - 40px);
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  margin: 0 auto;
}

/* ==================== 下部吸顶固定区与滚动区 ==================== */
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
  padding: 12px 4px 30px 4px;
  box-sizing: border-box;
}

.flight-list-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

:deep(.dark-select) .el-input__wrapper,
:deep(.dark-input) .el-input__wrapper {
  background-color: #1e293b !important;
  box-shadow: none !important;
}
:deep(.dark-select) .el-input__inner,
:deep(.dark-input) .el-input__inner {
  color: #38bdf8 !important;
  font-weight: bold;
}
.mini-width { width: 80px; }
.medium-width { width: 140px; }

.route-input-group {
  display: flex;
  align-items: center;
  background-color: #1e293b;
  border-radius: 4px;
  padding: 0 8px;
}
.route-input-group .dark-input { width: 130px; }
.transfer-icon { color: #64748b; margin: 0 4px; font-size: 16px; }

:deep(.dark-date-picker) {
  background-color: #1e293b !important;
  border: none !important;
  width: 240px !important;
}
:deep(.dark-date-picker) .el-range-input { color: #38bdf8 !important; font-weight: bold; }
.range-tip { color: #94a3b8; font-size: 12px; white-space: nowrap; }

/* 模式切换 Tab */
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
.mode-tab.active {
  box-shadow: inset 0 -3px 0 #0099ff;
}

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
.light-select { width: 140px; }
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
.sort-item.active {
  color: #00a2ff;
  font-weight: bold;
}
.sort-arrow { display: flex; flex-direction: column; font-size: 10px; }
.plane-decoration-icon {
  position: absolute;
  right: 20%;
  color: #cbd5e1;
  font-size: 24px;
  transform: rotate(90deg);
}

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

.airline-info-layout {
  display: flex;
  align-items: center;
}
.airline-logo-placeholder {
  width: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 15px;
}
.airline-plane-icon {
  font-size: 24px;
  color: #0099ff;
}

.time-block { width: 180px; }
.time-block.departure {
  text-align: right;
  margin-right: 20px;
}
.time-block.arrival {
  text-align: left;
  margin-left: 20px;
}
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
  max-width: 200px;
  min-width: 80px;
}
.line-bar {
  height: 2px;
  background-color: #0099ff;
  position: relative;
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
.clock-icon {
  font-size: 18px;
}

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
.currency {
  font-size: 16px;
  color: #1e293b;
  align-self: flex-end;
  margin-bottom: -6px;
}
.amount {
  font-size: 34px;
  font-weight: bold;
  color: #1e293b;
}
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
</style>
