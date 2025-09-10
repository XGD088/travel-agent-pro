// Travel Agent Pro - Business Hours Utility
// 营业时间工具类

export interface TimeRange {
  start: number  // 分钟数（从00:00开始）
  end: number    // 分钟数（从00:00开始，可能超过1440表示跨天）
}

export interface BusinessHoursStatus {
  isOpen: boolean | null  // true: 营业中, false: 已关闭, null: 无法判断
  displayText: string     // 显示文本
  statusType: 'open' | 'closed' | 'unknown'  // 状态类型
}

/**
 * 营业时间工具类
 */
export class BusinessHoursUtil {
  /**
   * 解析营业时间字符串，返回时间段数组
   * 支持格式：
   * - "10:30-01:00" - 单个时间段
   * - "12:00-14:00 18:00-22:00" - 空格分隔的多个时间段
   * - "09:00-12:00,14:00-18:00" - 逗号分隔的多个时间段
   */
  static parseOpenHours(openHoursRaw: string): TimeRange[] {
    if (!openHoursRaw) return []
    
    try {
      const segments = openHoursRaw.split(/[,\s]+/).filter(s => s.trim())
      const timeRanges: TimeRange[] = []
      
      for (const segment of segments) {
        const match = segment.match(/(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})/)
        if (match) {
          const [, startHour, startMin, endHour, endMin] = match
          let startMinutes = parseInt(startHour) * 60 + parseInt(startMin)
          let endMinutes = parseInt(endHour) * 60 + parseInt(endMin)
          
          // 处理跨天情况（如 16:00-01:00）
          if (endMinutes < startMinutes) {
            endMinutes += 24 * 60 // 加一天
          }
          
          timeRanges.push({
            start: startMinutes,
            end: endMinutes
          })
        }
      }
      
      return timeRanges
    } catch (error) {
      console.warn('营业时间解析失败:', openHoursRaw, error)
      return []
    }
  }

  /**
   * 将时间字符串转换为分钟数
   * @param timeStr 时间字符串，如 "09:30"
   * @returns 分钟数（从00:00开始）
   */
  static timeToMinutes(timeStr: string): number {
    const match = timeStr.match(/(\d{1,2}):(\d{2})/)
    if (!match) return 0
    const [, hour, min] = match
    return parseInt(hour) * 60 + parseInt(min)
  }

  /**
   * 校验活动时间是否在营业时间内
   * @param activityStart 活动开始时间字符串
   * @param activityEnd 活动结束时间字符串
   * @param openHoursRaw 营业时间原始字符串
   * @returns 是否营业中（true: 营业中, false: 已关闭, null: 无法判断）
   */
  static isActivityOpen(
    activityStart: string, 
    activityEnd: string, 
    openHoursRaw: string
  ): boolean | null {
    if (!openHoursRaw) return null
    
    const openRanges = this.parseOpenHours(openHoursRaw)
    if (openRanges.length === 0) return null
    
    const actStart = this.timeToMinutes(activityStart)
    const actEnd = this.timeToMinutes(activityEnd)
    
    // 检查活动时间是否完全在某个营业时间段内
    for (const range of openRanges) {
      if (actStart >= range.start && actEnd <= range.end) {
        return true
      }
    }
    
    return false
  }

  /**
   * 获取营业状态信息，用于UI显示
   * @param activityStart 活动开始时间
   * @param activityEnd 活动结束时间  
   * @param openHoursRaw 营业时间原始字符串
   * @param backendOpenOk 后端判断的营业状态
   * @param closedReason 关闭原因
   * @returns 营业状态信息
   */
  static getBusinessStatus(
    activityStart: string,
    activityEnd: string,
    openHoursRaw?: string,
    backendOpenOk?: boolean | null,
    closedReason?: string
  ): BusinessHoursStatus {
    // 如果有营业时间数据，使用前端校验结果
    if (openHoursRaw) {
      const frontendCheck = this.isActivityOpen(activityStart, activityEnd, openHoursRaw)
      
      if (frontendCheck === true) {
        return {
          isOpen: true,
          displayText: `营业中: ${openHoursRaw}`,
          statusType: 'open'
        }
      } else if (frontendCheck === false) {
        return {
          isOpen: false,
          displayText: `已关闭: ${openHoursRaw}`,
          statusType: 'closed'
        }
      } else {
        // 解析失败，显示原始营业时间
        return {
          isOpen: null,
          displayText: `营业时间: ${openHoursRaw}`,
          statusType: 'unknown'
        }
      }
    }
    
    // 没有营业时间数据，使用后端判断
    if (backendOpenOk === false) {
      return {
        isOpen: false,
        displayText: `已关闭: ${closedReason || '请确认营业时间'}`,
        statusType: 'closed'
      }
    }
    
    if (backendOpenOk === true) {
      return {
        isOpen: true,
        displayText: "营业中: 全天开放",
        statusType: 'open'
      }
    }
    
    // 完全没有营业时间信息
    return {
      isOpen: null,
      displayText: "营业时间: 未知",
      statusType: 'unknown'
    }
  }
}
