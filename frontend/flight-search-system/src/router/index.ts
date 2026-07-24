import { createRouter, createWebHistory } from 'vue-router'
import FlightSearch from '../views/FlightSearch.vue'
import PricePredictor from '../views/PricePredictor.vue'
import DestinationMap from '../views/DestinationMap.vue'
import Agent from '../views/Agent.vue'
import DataDashboard from '../views/DataDashboard.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
{
      path: '/',
      redirect: '/search'
    },
    {
      path: '/search',
      name: 'search',
      component: FlightSearch // 1. 航班搜索
    },
    {
      path: '/agent',
      name: 'agent',
      component: () => import('../views/Agent.vue') // 2. AI 智能体助手
    },
    {
      path: '/predict',
      name: 'predict',
      component: () => import('../views/PricePredictor.vue') // 3. 价格预测
    },
    {
      path: '/map',
      name: 'map',
      component: () => import('../views/DestinationMap.vue') // 4. 目的地地图
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DataDashboard.vue') // 5. 数据分析Dashboard
    }
  ]
})

export default router
