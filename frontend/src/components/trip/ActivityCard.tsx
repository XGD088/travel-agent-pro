// Travel Agent Pro - Activity Card Component
// 活动卡片组件

import React from 'react'
import { 
  MapPin, 
  DollarSign, 
  Lightbulb, 
  CloudRain,
  CheckCircle2 
} from 'lucide-react'
import { Card } from '../ui/Card'
import { Activity } from '../../lib/api'
import { formatCurrency, formatTime } from '../../lib/utils'

interface ActivityCardProps {
  activity: Activity
  index: number
}

export function ActivityCard({ activity, index }: ActivityCardProps) {
  const startTime = activity.start_time || `${9 + index * 2}:${index % 2 === 0 ? '00' : '30'}`
  const endTime = activity.end_time || `${10 + index * 2}:${index % 2 === 0 ? '30' : '00'}`

  return (
    <Card padding="md" hover className="animate-fade-in-up">
      <div className="flex gap-6">
        {/* 时间信息 */}
        <div className="w-24 text-right">
          <p className="font-bold text-lg text-foreground">
            {formatTime(startTime)}
          </p>
          <p className="text-sm text-muted-foreground">
            - {formatTime(endTime)}
          </p>
        </div>
        
        {/* 活动详情 */}
        <div className="flex-1">
          <h3 className="font-bold text-lg text-foreground mb-2">
            {activity.name}
          </h3>
          
          <div className="space-y-1.5 text-sm">
            {/* 营业状态 */}
            <div className="flex items-center gap-2 text-muted-foreground">
              <CheckCircle2 className="w-4 h-4 status-icon-success" />
              <span>
                {activity.open_ok === false 
                  ? `已关闭: ${activity.closed_reason || '请确认营业时间'}`
                  : '营业中: 全天开放'
                }
              </span>
            </div>
            
            {/* 位置信息 */}
            {activity.location && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <MapPin className="w-4 h-4 status-icon-info" />
                <span>位置: {activity.location}</span>
              </div>
            )}
            
            {/* 费用信息 - 只有当费用存在且大于0时才显示 */}
            {activity.estimated_cost && activity.estimated_cost > 0 && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <DollarSign className="w-4 h-4 status-icon-warning" />
                <span>预估费用: {formatCurrency(activity.estimated_cost)}</span>
              </div>
            )}
            
            {/* 活动描述/建议 */}
            <div className="flex items-center gap-2 text-muted-foreground">
              <Lightbulb className="w-4 h-4 status-icon-info" />
              <span>
                {activity.description || activity.tips || "适合游览，体验当地文化。"}
              </span>
            </div>
            
            {/* 替换原因（如果有） */}
            {activity.replacement_reason && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <CloudRain className="w-4 h-4 status-icon-rain" />
                <span>已替换: {activity.replacement_reason}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  )
}
