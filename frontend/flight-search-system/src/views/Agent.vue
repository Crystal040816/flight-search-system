<script setup lang="ts">
import { ref, nextTick } from 'vue'
import {
  Switch, Search, Operation, Refresh,
  SuccessFilled, Promotion, Clock, Cpu, User, Delete, Position, ChatDotRound
} from '@element-plus/icons-vue'

// 引入存放图片的相对路径
import skyBg from '../pictures/天空.jpg'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  time: string
}

// --- 顶部状态栏表单状态 ---
const tripType = ref('往返')
const passengers = ref('1人, 经济舱')
const fromCity = ref('伦敦 (LON)')
const toCity = ref('纽约 (NYC)')
const dateRange = ref(['2026-08-12', '2026-08-20'])

// --- 智能体模式切换 ---
const currentMode = ref('free') // free: 航线规划 / package: 策略分析

// --- 模拟的大模型状态与对话数据集 ---
const activeAgent = ref('VS')
const isLoading = ref(false)
const inputMessage = ref('')
const scrollContainer = ref<HTMLElement | null>(null)

const messageList = ref<Message[]>([
  {
    id: 1,
    role: 'assistant',
    content: '您好！我是您的 AI 智能飞行助手。我已经同步了您上方的行程规划（伦敦 ✈ 纽约）。我可以为您分析维珍航空的价格走势、规避转机延误风险，或者定制穷游转机方案。今天有什么可以帮您？',
    time: '14:05'
  }
])

// 快捷提示词组
const quickQueries = [
  '帮我规划一套伦敦到纽约的穷游转机航线',
  '预测一下今年国庆期间飞往东京的机票趋势',
  '航班延误险一般怎么赔付？'
]

// --- 自动滚动到底部 ---
const scrollToBottom = async () => {
  await nextTick()
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
  }
}

// --- 执行搜索（保持与机票页逻辑联动） ---
const handleSearch = () => {
  console.log('AI 同步搜索:', fromCity.value, toCity.value, dateRange.value)
  messageList.value.push({
    id: Date.now(),
    role: 'assistant',
    content: `已为您同步最新航线数据：${fromCity.value} 至 ${toCity.value}，日期：${dateRange.value ? dateRange.value.join(' 到 ') : '未定'}。正在重新评估该航线的低价策略...`,
    time: '现在'
  })
  scrollToBottom()
}

// --- 发送对话消息 ---
const handleSend = async (textToSend?: string) => {
  const content = textToSend || inputMessage.value.trim()
  if (!content || isLoading.value) return

  const now = new Date()
  const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`

  // 1. 推送用户气泡
  messageList.value.push({
    id: Date.now(),
    role: 'user',
    content: content,
    time: timeStr
  })

  if (!textToSend) inputMessage.value = ''
  await scrollToBottom()

  // 2. 触发 AI 思考加载
  isLoading.value = true

  try {
    await new Promise(resolve => setTimeout(resolve, 1200)) // 模拟大模型响应延迟

    messageList.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: `针对您提到的“${content}”，AI 建议：通常维珍航空在周二下午会释放一批国际特价舱位。结合当前的性价比评分为 10 分，建议您在单程价格低于 ¥4,500 时直接果断入手。`,
      time: timeStr
    })
  } catch (error) {
    console.error('AI 响应失败:', error)
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

// 清空历史
const clearHistory = () => {
  messageList.value = [messageList.value[0]]
}
</script>

<template>
  <div class="page-wrapper-non-scrollable" :style="{ backgroundImage: `url(${skyBg})` }">

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
        <el-icon><Search /></el-icon>同步
      </el-button>
    </div>

    <div class="main-content-centered-layer">
      <div class="flight-search-container">

        <div class="sticky-fixed-header">

          <div class="mode-toggle-wrapper">
            <div class="mode-tab free-style" :class="{ active: currentMode === 'free' }" @click="currentMode = 'free'">
              <el-icon class="mode-icon"><Operation /></el-icon>
              <span>智能航线规划</span>
            </div>
            <div class="mode-tab package-style" :class="{ active: currentMode === 'package' }" @click="currentMode = 'package'">
              <el-icon class="mode-icon"><Refresh /></el-icon>
              <span>机票策略分析</span>
            </div>
          </div>

          <div class="current-route-info-bar">
            <div class="info-left">
              <span class="route-txt">AI CO-PILOT ✈ 实时飞行大脑</span>
              <span class="date-txt">已连接全球大模型网络</span>
            </div>
            <div class="info-right-badge" style="background-color: #65a30d;">Agent</div>
          </div>

          <div class="filter-panel">
            <div class="filter-row">
              <span style="font-weight: bold; color: #334155; font-size: 14px;">大模型模型设定：</span>
              <el-select v-model="activeAgent" placeholder="知识库选择" class="light-select" style="width: 180px;">
                <el-option label="精通-维珍航空专家" value="VS" />
                <el-option label="精通-国际航协规章" value="IATA" />
                <el-option label="精通-全球穷游转机" value="LOW" />
              </el-select>
              <div style="flex: 1;"></div>
              <el-button size="small" type="danger" plain :icon="Delete" @click="clearHistory">
                清空对话历史
              </el-button>
            </div>
          </div>

          <div class="sort-navbar">
            <div class="sort-item active"><el-icon><Cpu /></el-icon> 实时语义解析</div>
            <div class="sort-item">大模型动态思考</div>
            <div class="plane-decoration-icon">✈</div>
          </div>
        </div>

        <div ref="scrollContainer" class="scrollable-flight-list-area">
          <div class="flight-list-wrapper">

            <div
              v-for="msg in messageList"
              :key="msg.id"
              class="flight-card message-card"
              :class="msg.role === 'user' ? 'user-card-style' : ''"
            >
              <div class="card-header">
                <div class="header-left">
                  <span class="lowest-tag" :style="{ backgroundColor: msg.role === 'user' ? '#1e293b' : '#ffedd5', color: msg.role === 'user' ? '#38bdf8' : '#ea580c' }">
                    {{ msg.role === 'assistant' ? 'AI 助理' : 'USER' }}
                  </span>
                  <span class="flight-meta">发送时间: {{ msg.time }}</span>
                </div>
                <div class="header-right-score" :style="{ color: msg.role === 'user' ? '#38bdf8' : '#65a30d' }">
                  <el-icon class="thumb-icon">
                    <Cpu v-if="msg.role === 'assistant'" />
                    <User v-else />
                  </el-icon>
                  <span>{{ msg.role === 'assistant' ? '10' : 'PRO' }}</span>
                </div>
              </div>

              <div class="card-body" style="padding: 10px 0;">
                <div class="message-text-p">
                  {{ msg.content }}
                </div>
              </div>
            </div>

            <div v-if="isLoading" class="flight-card message-card">
              <div class="card-header">
                <div class="header-left">
                  <span class="lowest-tag" style="background-color: #e0f2fe; color: #0369a1;">AI 正在思考</span>
                </div>
              </div>
              <div class="card-body">
                <div class="typing-dots">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>

          </div>
        </div>

        <div class="chat-input-sticky-footer">
          <div class="quick-hints-row" v-if="messageList.length <= 1">
            <div v-for="(hint, index) in quickQueries" :key="index" class="hint-tag" @click="handleSend(hint)">
              <el-icon><ChatDotRound /></el-icon>
              <span>{{ hint }}</span>
            </div>
          </div>

          <div class="input-container-box">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="2"
              placeholder="请输入您的问题，例如：“帮我看看8月份去纽约，坐哪趟航班舒适度最高？”"
              resize="none"
              @keydown.enter.prevent="handleSend()"
            />
            <el-button type="warning" class="select-btn send-btn-adjust" :loading="isLoading" @click="handleSend()">
              <el-icon style="margin-right: 4px;"><Position /></el-icon> 发送指令
            </el-button>
          </div>
        </div>

      </div> <!-- 结束 flight-search-container[cite: 3] -->
    </div> <!-- 结束 main-content-centered-layer[cite: 3] -->
  </div> <!-- 结束 page-wrapper-non-scrollable[cite: 3] -->
</template>

<style scoped>
.page-wrapper-non-scrollable {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 240px;
  right: 0;
  overflow: hidden;
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

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

.search-sticky-bar :deep(.el-input__wrapper) { height: 32px !important; }
.search-btn { height: 32px !important; line-height: 32px !important; padding: 0 20px !important; }

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

.sticky-fixed-header { display: flex; flex-direction: column; flex-shrink: 0; z-index: 10; }

.scrollable-flight-list-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 4px 10px 4px;
  box-sizing: border-box;
}

.flight-list-wrapper { display: flex; flex-direction: column; gap: 14px; width: 100%; }

:deep(.dark-select) .el-input__wrapper,
:deep(.dark-input) .el-input__wrapper { background-color: #1e293b !important; box-shadow: none !important; }
:deep(.dark-select) .el-input__inner,
:deep(.dark-input) .el-input__inner { color: #38bdf8 !important; font-weight: bold; }
.mini-width { width: 80px; }
.medium-width { width: 140px; }
.route-input-group { display: flex; align-items: center; background-color: #1e293b; border-radius: 4px; padding: 0 8px; }
.route-input-group .dark-input { width: 130px; }
.transfer-icon { color: #64748b; margin: 0 4px; font-size: 16px; }
:deep(.dark-date-picker) { background-color: #1e293b !important; border: none !important; width: 240px !important; }
:deep(.dark-date-picker) .el-range-input { color: #38bdf8 !important; font-weight: bold; }
.range-tip { color: #94a3b8; font-size: 12px; white-space: nowrap; }

.mode-toggle-wrapper { display: flex; margin-top: 8px; gap: 4px; }
.mode-tab { flex: 1; height: 48px; display: flex; align-items: center; justify-content: center; gap: 8px; cursor: pointer; font-size: 15px; font-weight: bold; border-radius: 6px 6px 0 0; transition: all 0.2s; }
.free-style { background-color: #ffffff; color: #1e293b; }
.package-style { background-color: #0a2240; color: #94a3b8; }
.mode-tab.active { box-shadow: inset 0 -3px 0 #0099ff; }

.current-route-info-bar { background-color: #00a2ff; color: #ffffff; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; font-weight: bold; position: relative; }
.route-txt { font-size: 16px; margin-right: 12px; }
.date-txt { font-size: 14px; opacity: 0.9; }
.info-right-badge { background-color: #ff9900; padding: 10px 30px; margin-right: -20px; clip-path: polygon(15% 0%, 100% 0%, 100% 100%, 0% 100%); }

.filter-panel { background-color: #ffffff; border-bottom: 1px solid #e2e8f0; padding: 12px 20px; }
.filter-row { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
.light-select { width: 140px; }
:deep(.light-select) .el-input__wrapper { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; }

.sort-navbar { background-color: #24292e; height: 40px; display: flex; align-items: center; padding: 0 20px; position: relative; border-top: 3px solid #00a2ff; }
.sort-item { color: #bcbcbc; font-size: 14px; padding: 0 20px; border-right: 1px solid #3f4448; cursor: pointer; display: flex; align-items: center; gap: 4px; }
.sort-item.active { color: #00a2ff; font-weight: bold; }
.plane-decoration-icon { position: absolute; right: 20%; color: #cbd5e1; font-size: 24px; transform: rotate(90deg); }

.flight-card {
  background-color: #ffffff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 14px 20px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}

.user-card-style {
  background-color: #1b222d !important;
  border-color: #2d3748 !important;
}
.user-card-style .flight-meta { color: #94a3b8 !important; }
.user-card-style .message-text-p { color: #e2e8f0 !important; }

.message-text-p {
  font-size: 15px;
  line-height: 1.7;
  color: #1e293b;
  white-space: pre-wrap;
  word-break: break-all;
}

.chat-input-sticky-footer {
  background-color: transparent;
  padding: 10px 0 24px 0;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quick-hints-row { display: flex; gap: 10px; flex-wrap: wrap; }
.hint-tag {
  background-color: rgba(255, 255, 255, 0.9);
  border: 1px solid #cbd5e1;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  color: #334155;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}
.hint-tag:hover { background-color: #ffffff; border-color: #00a2ff; color: #00a2ff; }

.input-container-box {
  background-color: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.input-container-box :deep(.el-textarea__inner) {
  box-shadow: none !important;
  border: none !important;
  padding: 6px 8px;
  font-size: 15px;
  color: #1e293b;
}

.send-btn-adjust {
  padding: 8px 24px !important;
  height: 36px !important;
  border-radius: 18px !important;
  font-size: 14px !important;
}

.typing-dots { display: flex; align-items: center; gap: 5px; height: 24px; padding-left: 4px; }
.typing-dots span { width: 6px; height: 6px; background-color: #00a2ff; border-radius: 50%; animation: dotBounce 1.4s infinite ease-in-out both; }
.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes dotBounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); }
}
</style>
