// Travel Agent Pro - Date Picker Component
// 日期选择器组件

import React from 'react'
import { useDatePicker } from '../../hooks/useDatePicker'
import { useModal, useFormState } from '../../stores/uiStore'

export function DatePicker() {
  const { isOpen } = useModal()
  const { dateError } = useFormState()
  
  // 使用自定义hook处理日期选择器逻辑
  useDatePicker(isOpen)

  return (
    <div>
      <label className="block text-sm font-medium text-[var(--muted-foreground)] mb-1">
        日期范围 <span className="text-red-500">*</span>
      </label>
      <input 
        id="date-picker" 
        type="text" 
        placeholder="选择您的旅行日期" 
        className={`w-full p-2 bg-[var(--input)] border rounded-md cursor-pointer transition-colors ${
          dateError 
            ? 'border-red-500 focus:border-red-500' 
            : 'border-[var(--border)] focus:border-blue-500'
        }`}
        readOnly
      />
      {dateError && (
        <p className="mt-1 text-sm text-red-500 flex items-center gap-1">
          <span className="text-xs">⚠️</span>
          {dateError}
        </p>
      )}
    </div>
  )
}


