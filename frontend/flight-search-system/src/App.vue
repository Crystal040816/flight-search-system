<script setup lang="ts">
import { RouterView } from 'vue-router'
import { Compass, Search, TrendCharts, Cpu, Location, Odometer } from '@element-plus/icons-vue'

const components = {
  Compass,
  Search,
  TrendCharts,
  Cpu,
  Location,
  Odometer
}
</script>

<template>
  <div id="app">
    <el-menu
      router
      default-active="/search"
      background-color="#12161f"
      text-color="#a3b8cc"
      active-text-color="#409eff"
      class="nav-menu-sidebar"
    >
      <div class="logo-area">
        <el-icon class="logo-icon"><Compass /></el-icon>
        <span class="logo-text">智能机票系统</span>
      </div>

      <!-- 纵向菜单项 -->
      <el-menu-item index="/search">
        <el-icon><Search /></el-icon>
        <span>航班搜索</span>
      </el-menu-item>

      <el-menu-item index="/predict">
        <el-icon><TrendCharts /></el-icon>
        <span>低价走势</span>
      </el-menu-item>

      <el-menu-item index="/agent">
        <el-icon><Cpu /></el-icon>
        <span>AI助手</span>
      </el-menu-item>

      <el-menu-item index="/map">
        <el-icon><Location /></el-icon>
        <span>飞去哪儿</span>
      </el-menu-item>

      <el-menu-item index="/dashboard">
        <el-icon><Odometer /></el-icon>
        <span>数据看板</span>
      </el-menu-item>
    </el-menu>

    <!-- 右侧页面渲染主体区域 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style>
html, body {
  margin: 0 !important;
  padding: 0 !important;
  background-color: #0b0e14;
  color: #e2e8f0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  height: 100% !important;
  width: 100% !important;
  overflow: hidden;
}

#app {
  height: 100% !important;
  width: 100% !important;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: row;
  overflow: hidden;
  margin: 0 !important;
  padding: 0 !important;
}

.nav-menu-sidebar {
  width: 240px !important;
  min-width: 240px !important;
  height: 100% !important;
  border-right: 1px solid #1e293b !important;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  padding-top: 20px;
  margin: 0 !important;
  border-left: none !important;
}

.logo-area {
  display: flex;
  align-items: center;
  color: #ffffff;
  font-weight: bold;
  font-size: 15px;
  letter-spacing: 0.5px;
  padding: 0 20px 20px 20px;
  border-bottom: 1px solid #1e293b;
  margin-bottom: 16px;
}

.logo-icon {
  font-size: 22px;
  color: #409eff;
  margin-right: 8px;
}

.main-content {
  flex: 1;
  width: 0;
  height: 100%;
  position: relative;
  padding: 0 !important;
  margin: 0 !important;
  overflow: hidden;
  background-color: transparent;
}

.el-menu-item {
  height: 50px !important;
  line-height: 50px !important;
  margin: 4px 12px;
  border-radius: 6px;
  display: flex;
  align-items: center;
}

.el-menu-item:hover {
  background-color: #1e2533 !important;
  color: #ffffff !important;
}
</style>
