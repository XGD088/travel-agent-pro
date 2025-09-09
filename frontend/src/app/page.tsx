// Travel Agent Pro - Main Page (重构版本)
// 从709行巨型组件重构为清洁的组件组合

'use client'

import React from 'react'
import { AppLayout } from '../components/layout/AppLayout'
import { Sidebar } from '../components/layout/Sidebar'
import { MainContent } from '../components/layout/MainContent'
import { TripPlanModal } from '../components/forms/TripPlanModal'
import { useBackendHealth } from '../hooks/useBackendHealth'

export default function Home() {
  // 初始化后端健康检查
  useBackendHealth()

  return (
    <>
      <AppLayout>
        <Sidebar />
        <MainContent />
      </AppLayout>
      
      {/* 全局模态框 */}
      <TripPlanModal />
    </>
  )
}


