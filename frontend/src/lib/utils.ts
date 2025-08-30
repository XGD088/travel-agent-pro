// Travel Agent Pro - Utility Functions
// 通用工具函数

import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

// 合并类名工具函数
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 日期格式化工具
export function formatDate(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 货币格式化工具
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
}

// 时间格式化工具
export function formatTime(time: string): string {
  const [hours, minutes] = time.split(':')
  return `${hours}:${minutes}`
}

// 距离格式化工具
export function formatDistance(distance: number): string {
  if (distance >= 1) {
    return `${distance.toFixed(1)}km`
  } else {
    return `${(distance * 1000).toFixed(0)}m`
  }
}

// 交通方式推断工具
export function inferTransportMode(distance?: number, driveTime?: number) {
  if (!driveTime || !distance) {
    return { mode: 'walk', icon: 'Footprints', text: '步行' }
  }
  
  const kmPerMin = distance / driveTime
  
  if (kmPerMin < 0.1) {
    return { mode: 'walk', icon: 'Footprints', text: '步行' }
  } else if (kmPerMin < 0.5) {
    return { mode: 'transit', icon: 'Train', text: '地铁' }
  } else {
    return { mode: 'car', icon: 'Car', text: '驾车' }
  }
}

