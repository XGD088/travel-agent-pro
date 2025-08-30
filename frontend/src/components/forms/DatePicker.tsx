// Travel Agent Pro - Date Picker Component
// 日期选择器组件

import React from 'react'
import { useDatePicker } from '../../hooks/useDatePicker'
import { useModal } from '../../stores/uiStore'

export function DatePicker() {
  const { isOpen } = useModal()
  
  // 使用自定义hook处理日期选择器逻辑
  useDatePicker(isOpen)

  return (
    <div>
      <label className="block text-sm font-medium text-[var(--muted-foreground)] mb-1">
        日期范围
      </label>
      <input 
        id="date-picker" 
        type="text" 
        placeholder="选择您的旅行日期" 
        className="w-full p-2 bg-[var(--input)] border border-[var(--border)] rounded-md cursor-pointer"
        readOnly
      />
    </div>
  )
}

