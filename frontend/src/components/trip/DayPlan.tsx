// Travel Agent Pro - Day Plan Component
// 单日行程组件

import React from 'react'
import { Clock } from 'lucide-react'
import { Card } from '../ui/Card'
import { ActivityCard } from './ActivityCard'
import { TimelineConnector } from './TimelineConnector'
import { DayPlan as DayPlanType } from '../../lib/api'
import { formatCurrency } from '../../lib/utils'

interface DayPlanProps {
  dayPlan: DayPlanType
  dayIndex: number
}

export function DayPlan({ dayPlan, dayIndex }: DayPlanProps) {
  return (
    <div 
      className="space-y-6" 
      style={{ animationDelay: `${dayIndex * 200}ms` }}
    >
      {/* 日期标题 */}
      <h2 className="text-xl font-bold text-foreground mb-4">
        第{dayIndex + 1}天: {dayPlan.date} · {dayPlan.day_title}
      </h2>
      
      {/* 活动列表 */}
      <div className="space-y-0">
        {dayPlan.activities.map((activity, actIndex) => (
          <React.Fragment key={actIndex}>
            {/* 活动卡片 */}
            <ActivityCard 
              activity={activity} 
              index={actIndex} 
            />
            
            {/* 时间轴连接器（不是最后一个活动才显示） */}
            {actIndex < dayPlan.activities.length - 1 && (
              <TimelineConnector 
                nextActivity={dayPlan.activities[actIndex + 1]} 
              />
            )}
          </React.Fragment>
        ))}
      </div>
      
      {/* 当日总结 */}
      {dayPlan.daily_summary && (
        <Card padding="md" className="bg-[var(--muted)] border border-[var(--border)]">
          <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
            <Clock className="w-4 h-4" />
            当日总结
          </h4>
          <p className="text-sm text-muted-foreground">
            {dayPlan.daily_summary}
          </p>
          {dayPlan.estimated_daily_cost && dayPlan.estimated_daily_cost > 0 && (
            <p className="text-sm text-muted-foreground mt-2">
              <strong>当日预算:</strong> {formatCurrency(dayPlan.estimated_daily_cost)}
            </p>
          )}
        </Card>
      )}
    </div>
  )
}
