<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Switch, Cpu, User, Position, ChatDotRound, Delete
} from '@element-plus/icons-vue'

// 引入图片与 API
import skyBg from '../pictures/天空.jpg'
import { getOriginCities } from '@/api/origins'
import { getDestinationCities } from '@/api/destinations'
import { getAvailableDates } from '@/api/dates'
import { getRecommendFlights, type RecommendItem } from '@/api/recommend'

// 选项数据
const originOptions = ref<{ label: string; value: string }[]>([])
const destOptions = ref<{ label: string; value: string }[]>([])
const availableDates = ref<string[]>([])

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  time: string
}

// --- 统一响应式变量命名（重点：统一使用 departureDate） ---
const fromCity = ref('')
const toCity = ref('')
const departureDate = ref('')

const isLoading = ref(false)
const scrollContainer = ref<HTMLElement | null>(null)

const getCurrentTime = () => {
  const now = new Date()
  return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
}

const messageList = ref<Message[]>([
  {
    id: 1,
    role: 'assistant',
    content: '您好！我是您的 AI 智能飞行助手。请先确认对话框中的出发机场、目的地机场及出发日期，我将为您精准推荐最优质的航班方案。',
    time: getCurrentTime()
  }
])

// 切换出发地与目的地
const swapCities = () => {
  const temp = fromCity.value
  fromCity.value = toCity.value
  toCity.value = temp
}

// 自动滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
  }
}

// 格式化文本
const formatRecommendationToText = (recommendations: RecommendItem[]) => {
  if (!recommendations || recommendations.length === 0) {
    return '抱歉，系统暂未为您检索到满足条件的合适航班推荐，建议更换出发日期或城市重试。'
  }

  let text = `为您找到了 ${recommendations.length} 条高匹配度的优质航班推荐：\n\n`

  recommendations.forEach((item, index) => {
    const f = item.flight
    const stopsText = f.stops === 0 ? '直飞' : `经停 ${f.stops} 次`
    const cabinText = f.cabinSummary || f.cabin || '经济舱'
    const depCity = f.departureCity ? `${f.departureCity}(${f.departure})` : f.departure
    const destCity = f.destinationCity ? `${f.destinationCity}(${f.destination})` : f.destination

    text += `【推荐 ${item.rank || index + 1}】 ${f.airline} (${f.airlineCode}) - 机型 ${f.aircraftModel || '未知'}\n`
    text += `✈ 航线: ${depCity} ➔ ${destCity}\n`
    text += `📅 出发日期: ${f.departureTime || departureDate.value} (${stopsText})\n`
    text += `💰 全网最低价: $${f.lowestPrice} (均价: $${f.avgPrice}) | 舱位: ${cabinText} | 余票: ${f.seatsRemaining || '充足'} 张\n`
    text += `💡 推荐理由: ${item.reason} (综合评分 ${f.totalScore})\n\n`
  })

  text += '您可以告诉我您心仪的航班，我可为您提供进一步的解答！'
  return text
}

// 发送逻辑
const handleSend = async (customPrompt?: string) => {
  if (isLoading.value) return

  // ✅ 修正：使用正确变量 departureDate
  if (!fromCity.value || !toCity.value || !departureDate.value) {
    ElMessage.warning('请确保已选择出发地、目的地和出发日期！')
    return
  }

  const timeStr = getCurrentTime()
  const displayContent = customPrompt
    ? customPrompt
    : `查询从 ${fromCity.value} 到 ${toCity.value} (${departureDate.value}) 的推荐航班`

  messageList.value.push({
    id: Date.now(),
    role: 'user',
    content: displayContent,
    time: timeStr
  })

  await scrollToBottom()
  isLoading.value = true

  const formatCode = (val: string) => {
    const match = val.match(/\(([^)]+)\)/)
    return match ? match[1] : val.trim()
  }

  try {
    const res = await getRecommendFlights({
      departure: formatCode(fromCity.value),
      destination: formatCode(toCity.value),
      flightDate: departureDate.value,
      preferences: {
        preferDirect: true,
        preferLowPrice: true,
        preferShortDuration: false
      }
    })

    let assistantReply = ''
    if (res.data.code === 200 && res.data.data) {
      assistantReply = formatRecommendationToText(res.data.data.recommendations)
    } else {
      assistantReply = `检索推荐时遇到问题：${res.data.message || '未知错误'}`
    }

    messageList.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: assistantReply,
      time: getCurrentTime()
    })
  } catch (error) {
    console.error('获取智能推荐失败:', error)
    messageList.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: '服务请求超时或出错，请检查后重新尝试。',
      time: getCurrentTime()
    })
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

// 清空历史
const clearHistory = () => {
  messageList.value = [messageList.value[0]]
}

// 加载初始数据
const loadOrigins = async () => {
  try {
    const res = await getOriginCities()
    if (res.data.code === 200) {
      originOptions.value = res.data.data.map((city: string) => ({ label: city, value: city }))
    }
  } catch (e) { console.error(e) }
}

const loadDestinations = async () => {
  try {
    const res = await getDestinationCities()
    if (res.data.code === 200) {
      destOptions.value = res.data.data.map((city: string) => ({ label: city, value: city }))
    }
  } catch (e) { console.error(e) }
}

const loadDates = async () => {
  try {
    const res = await getAvailableDates()
    if (res.data.code === 200) {
      availableDates.value = res.data.data || []
      if (availableDates.value.length > 0 && !departureDate.value) {
        departureDate.value = availableDates.value[0]
      }
    }
  } catch (e) { console.error(e) }
}

const disabledDate = (time: Date) => {
  if (availableDates.value.length === 0) return false
  const year = time.getFullYear()
  const month = String(time.getMonth() + 1).padStart(2, '0')
  const day = String(time.getDate()).padStart(2, '0')
  return !availableDates.value.includes(`${year}-${month}-${day}`)
}

onMounted(() => {
  loadOrigins()
  loadDestinations()
  loadDates()
})
</script>

<template>
  <div class="page-wrapper-non-scrollable" :style="{ backgroundImage: `url(${skyBg})` }">
    <div class="main-content-centered-layer">
      <div class="flight-search-container">

        <!-- 头部 -->
        <div class="sticky-fixed-header">
          <div class="current-route-info-bar">
            <span class="route-txt">AI CO-PILOT ✈ 实时推荐智能体</span>
          </div>
          <div class="filter-panel">
            <div class="filter-row">
              <span style="font-weight: bold; color: #334155; font-size: 14px;">当前匹配路线：</span>
              <span style="color: #0284c7; font-weight: bold;">
                {{ fromCity || '未填出发地' }} ➔ {{ toCity || '未填目的地' }} ({{ departureDate || '未选日期' }})
              </span>
              <div style="flex: 1;"></div>
              <el-button size="small" type="danger" plain :icon="Delete" @click="clearHistory">
                清空对话历史
              </el-button>
            </div>
          </div>
        </div>

        <!-- 聊天区域 -->
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
                  <span class="flight-meta">时间: {{ msg.time }}</span>
                </div>
                <div class="header-right-score" :style="{ color: msg.role === 'user' ? '#38bdf8' : '#65a30d' }">
                  <el-icon><Cpu v-if="msg.role === 'assistant'" /><User v-else /></el-icon>
                  <span>{{ msg.role === 'assistant' ? '推荐' : '提问' }}</span>
                </div>
              </div>

              <div class="card-body" style="padding: 10px 0;">
                <div class="message-text-p">{{ msg.content }}</div>
              </div>
            </div>

            <div v-if="isLoading" class="flight-card message-card">
              <div class="card-header">
                <span class="lowest-tag" style="background-color: #e0f2fe; color: #0369a1;">AI 正在计算最佳推荐航班...</span>
              </div>
              <div class="card-body"><div class="typing-dots"><span></span><span></span><span></span></div></div>
            </div>
          </div>
        </div>

        <!-- 底部输入框区域 -->
        <div class="chat-input-sticky-footer">
          <div class="quick-hints-row" v-if="messageList.length <= 1">
            <div v-for="(hint, index) in quickQueries" :key="index" class="hint-tag" @click="handleSend(hint)">
              <el-icon><ChatDotRound /></el-icon>
              <span>{{ hint }}</span>
            </div>
          </div>

          <div class="input-container-box">
            <div class="inline-search-bar">

              <!-- 出发城市（使用 inline style 强制锁定宽度，防止 CSS 失效） -->
              <el-select v-model="fromCity" placeholder="出发城市" class="city-select-box" style="width: 150px;">
                <el-option v-for="item in originOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>

              <el-icon class="transfer-icon" @click="swapCities"><Switch /></el-icon>

              <!-- 到达城市 -->
              <el-select v-model="toCity" placeholder="到达城市" class="city-select-box" style="width: 150px;">
                <el-option v-for="item in destOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>

              <!-- 出发日期 -->
              <el-date-picker
                v-model="departureDate"
                type="date"
                placeholder="选择日期"
                class="date-select-box"
                style="width: 170px;"
                value-format="YYYY-MM-DD"
                :disabled-date="disabledDate"
              />

              <div class="flex-spacer"></div>

              <el-button type="warning" class="send-btn" :loading="isLoading" @click="handleSend()">
                <el-icon style="margin-right: 6px;"><Position /></el-icon> 获取推荐
              </el-button>

            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrapper-non-scrollable {
  position: fixed;
  top: 0; bottom: 0; left: 240px; right: 0;
  overflow: hidden;
  background-size: cover; background-position: center; background-repeat: no-repeat;
  box-sizing: border-box;
  display: flex; flex-direction: column;
}

.main-content-centered-layer {
  flex: 1; width: 100%; height: 100%;
  display: flex; justify-content: center; align-items: flex-start;
  overflow: hidden; padding-top: 10px;
}

.flight-search-container {
  width: 1150px; max-width: calc(100% - 40px); height: 100%;
  display: flex; flex-direction: column; box-sizing: border-box; margin: 0 auto;
}

.sticky-fixed-header { display: flex; flex-direction: column; flex-shrink: 0; z-index: 10; }

.scrollable-flight-list-area {
  flex: 1; overflow-y: auto; overflow-x: hidden;
  padding: 12px 4px 10px 4px; box-sizing: border-box;
}

.flight-list-wrapper { display: flex; flex-direction: column; gap: 14px; width: 100%; }

.current-route-info-bar { background-color: #00a2ff; color: #ffffff; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; font-weight: bold; border-radius: 8px 8px 0 0; }
.route-txt { font-size: 16px; }

.filter-panel { background-color: #ffffff; border-bottom: 1px solid #e2e8f0; padding: 12px 20px; }
.filter-row { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }

.flight-card { background-color: #ffffff; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); padding: 14px 20px; border: 1px solid #e2e8f0; }
.card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #e2e8f0; padding-bottom: 8px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.lowest-tag { padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
.flight-meta { font-size: 12px; color: #64748b; }
.header-right-score { display: flex; align-items: center; gap: 4px; font-weight: bold; }

.user-card-style { background-color: #1b222d !important; border-color: #2d3748 !important; }
.user-card-style .flight-meta { color: #94a3b8 !important; }
.user-card-style .message-text-p { color: #e2e8f0 !important; }

.message-text-p { font-size: 15px; line-height: 1.7; color: #1e293b; white-space: pre-wrap; word-break: break-all; }

.chat-input-sticky-footer { background-color: transparent; padding: 10px 0 20px 0; flex-shrink: 0; display: flex; flex-direction: column; gap: 10px; }
.quick-hints-row { display: flex; gap: 10px; flex-wrap: wrap; }
.hint-tag { background-color: rgba(255, 255, 255, 0.9); border: 1px solid #cbd5e1; padding: 6px 14px; border-radius: 20px; font-size: 13px; color: #334155; cursor: pointer; display: flex; align-items: center; gap: 6px; }

/* 底部框核心 */
.input-container-box {
  background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 10px 16px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}
.inline-search-bar { display: flex; align-items: center; gap: 12px; width: 100%; }
.flex-spacer { flex: 1; }

/* 双重锁死输入框宽度 */
:deep(.city-select-box) { width: 150px !important; }
:deep(.date-select-box) { width: 170px !important; }

.transfer-icon { color: #64748b; font-size: 16px; cursor: pointer; }
.send-btn { padding: 0 24px !important; height: 40px !important; border-radius: 20px !important; font-weight: bold; background-color: #f59e0b !important; border: none !important; }

.typing-dots { display: flex; align-items: center; gap: 5px; height: 24px; }
.typing-dots span { width: 6px; height: 6px; background-color: #00a2ff; border-radius: 50%; animation: dotBounce 1.4s infinite ease-in-out both; }
.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes dotBounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1.0); } }
</style>

```
