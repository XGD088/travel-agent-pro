// Travel Agent Pro - Sidebar Component
// 侧边栏组件

import React from 'react'
import { Edit3, Map, Rocket } from 'lucide-react'
import { Button } from '../ui/Button'
import { TripPlanDetails } from '../trip/TripPlanDetails'
import { useTripPlan } from '../../stores/tripStore'
import { useModal } from '../../stores/uiStore'

export function Sidebar() {
  const tripPlan = useTripPlan()
  const { open: openModal } = useModal()
  const hasPlan = !!tripPlan

  return (
    <aside className="w-1/3 lg:w-1/4 bg-[var(--sidebar)] p-8 border-r border-[var(--sidebar-border)] flex flex-col gap-8">
      {/* 品牌标题 */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--foreground)]">
          Travel Agent Pro
        </h1>
        <p className="text-sm text-[var(--muted-foreground)] mt-1">
          您的智能行程规划助手
        </p>
      </div>
      
      {/* 行程详情 */}
      <div className="space-y-6">
        <h2 className="text-lg font-semibold text-[var(--foreground)]">
          您的计划
        </h2>
        <div id="plan-details-container">
          <TripPlanDetails />
        </div>
      </div>
      
      {/* 操作按钮 */}
      <div className="mt-auto space-y-3">
        <Button 
          onClick={openModal}
          className="w-full"
          icon={hasPlan ? <Edit3 className="w-4 h-4" /> : <Rocket className="w-4 h-4" />}
        >
          {hasPlan ? "优化行程" : "新建行程"}
        </Button>
        
        {hasPlan && (
          <Button 
            variant="secondary"
            className="w-full"
            icon={<Map className="w-4 h-4" />}
          >
            在地图上查看
          </Button>
        )}
      </div>
    </aside>
  )
}


