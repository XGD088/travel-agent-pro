// Travel Agent Pro - Timeline Connector Component
// 时间轴连接器组件

import React from 'react'
import { Car, Footprints, Train } from 'lucide-react'
import { Activity } from '../../lib/api'
import { formatDistance, inferTransportMode } from '../../lib/utils'

interface TimelineConnectorProps {
  nextActivity: Activity
}

export function TimelineConnector({ nextActivity }: TimelineConnectorProps) {
  const driveTime = nextActivity.drive_time_min_from_prev
  const distance = nextActivity.distance_km_from_prev
  
  // 推断交通方式
  const transport = inferTransportMode(distance, driveTime)
  
  // 选择对应的图标组件
  const IconComponent = transport.icon === 'Footprints' ? Footprints :
                       transport.icon === 'Train' ? Train : Car
  
  // 构建显示文本
  let displayText = ''
  
  if (driveTime && distance) {
    displayText = `${transport.text} ${driveTime}分钟 (${formatDistance(distance)})`
  } else if (driveTime) {
    displayText = `${transport.text} ${driveTime}分钟`
  } else if (distance) {
    displayText = `${transport.text} ${formatDistance(distance)}`
  } else {
    displayText = '步行 / 地铁 15分钟' // 默认值
  }

  return (
    <div className="timeline-connector">
      <span className="timeline-connector-text">
        <IconComponent className="w-4 h-4" />
        {displayText}
      </span>
    </div>
  )
}

