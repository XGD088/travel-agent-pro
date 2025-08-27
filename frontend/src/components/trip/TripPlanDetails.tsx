// Travel Agent Pro - Trip Plan Details Component
// 行程详情组件（侧边栏显示）

import React from 'react'
import { useTripPlan } from '../../stores/tripStore'
import { formatCurrency } from '../../lib/utils'

export function TripPlanDetails() {
  const tripPlan = useTripPlan()

  if (!tripPlan) {
    return (
      <p className="text-sm text-muted-foreground">
        当前没有行程，点击下方按钮开始您的第一次规划。
      </p>
    )
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="text-sm font-medium text-muted-foreground">
          目的地
        </label>
        <p className="text-base font-semibold text-foreground mt-1">
          {tripPlan.destination}
        </p>
      </div>
      
      <div>
        <label className="text-sm font-medium text-muted-foreground">
          日期
        </label>
        <p className="text-base font-semibold text-foreground mt-1">
          {tripPlan.start_date} - {tripPlan.end_date}
        </p>
      </div>
      
      <div>
        <label className="text-sm font-medium text-muted-foreground">
          旅行主题
        </label>
        <p className="text-base font-semibold text-foreground mt-1">
          {tripPlan.theme}
        </p>
      </div>
      
      <div>
        <label className="text-sm font-medium text-muted-foreground">
          总预算
        </label>
        <p className="text-base font-semibold text-foreground mt-1">
          约 {formatCurrency(tripPlan.total_estimated_cost)}
        </p>
      </div>
    </div>
  )
}
