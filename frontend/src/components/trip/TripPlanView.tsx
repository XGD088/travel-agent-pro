// Travel Agent Pro - Trip Plan View Component
// 行程展示组件（主内容区域）

import React, { useEffect } from 'react'
import { Download, Share2 } from 'lucide-react'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { DayPlan } from './DayPlan'
import { useTripPlan } from '../../stores/tripStore'

export function TripPlanView() {
  const tripPlan = useTripPlan()

  // 初始化渐现动画
  useEffect(() => {
    const initializeAnimations = () => {
      const staggerContainer = document.querySelector('.stagger-reveal')
      if (staggerContainer) {
        const elements = Array.from(staggerContainer.children)
        elements.forEach((el, i) => {
          (el as HTMLElement).style.animationDelay = `${i * 200}ms`
        })
      }
    }

    if (tripPlan) {
      setTimeout(initializeAnimations, 100)
    }
  }, [tripPlan])

  if (!tripPlan) {
    return null
  }

  return (
    <>
      {/* 行程标题和操作 */}
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground">
            您的{tripPlan.destination}之旅
          </h1>
          <p className="text-muted-foreground mt-1">
            已为您智能优化 · {tripPlan.duration_days}天行程
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button 
            variant="secondary"
            icon={<Download className="w-4 h-4" />}
          >
            导出
          </Button>
          <Button 
            variant="secondary"
            icon={<Share2 className="w-4 h-4" />}
          >
            分享
          </Button>
        </div>
      </header>
      
      {/* 行程总览 */}
      {tripPlan.plan_rationale && (
        <Card padding="md" className="mb-6">
          <h3 className="text-lg font-semibold mb-3">规划思路</h3>
          <p className="text-muted-foreground">{tripPlan.plan_rationale}</p>
        </Card>
      )}
      
      {/* 每日行程 */}
      <div className="stagger-reveal space-y-12">
        {tripPlan.daily_plans.map((dayPlan, dayIndex) => (
          <DayPlan 
            key={dayPlan.date} 
            dayPlan={dayPlan} 
            dayIndex={dayIndex} 
          />
        ))}
      </div>
      
      {/* 总体建议 */}
      {tripPlan.general_tips && tripPlan.general_tips.length > 0 && (
        <Card padding="md" className="mt-6">
          <h3 className="text-lg font-semibold mb-3">出行建议</h3>
          <ul className="space-y-2">
            {tripPlan.general_tips.map((tip, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <span className="text-[var(--primary)] mt-1">•</span>
                <span className="text-muted-foreground">{tip}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </>
  )
}


