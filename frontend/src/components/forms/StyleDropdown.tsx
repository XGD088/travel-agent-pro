// Travel Agent Pro - Style Dropdown Component
// 旅行风格下拉框组件

import React, { useEffect } from 'react'
import { ChevronDown } from 'lucide-react'
import { useStyleDropdown } from '../../stores/uiStore'

interface StyleOption {
  value: string
  icon: string
  text: string
  description: string
}

const styleOptions: StyleOption[] = [
  { value: 'relaxed', icon: '🧘', text: '轻松', description: '每日2-3个活动' },
  { value: 'packed', icon: '🏃', text: '紧凑', description: '每日4-5个活动' },
  { value: 'business', icon: '👔', text: '商务', description: '高效、含会议时间' }
]

export function StyleDropdown() {
  const { 
    isOpen, 
    selectedStyle, 
    toggle, 
    close, 
    setStyle 
  } = useStyleDropdown()

  const selectedOption = styleOptions.find(opt => opt.value === selectedStyle) || styleOptions[0]

  // 处理点击外部关闭下拉菜单
  useEffect(() => {
    const handleDocumentClick = () => {
      close()
    }

    if (isOpen) {
      document.addEventListener('click', handleDocumentClick)
      return () => document.removeEventListener('click', handleDocumentClick)
    }
  }, [isOpen]) // 移除close依赖，因为它是稳定的Zustand函数

  return (
    <div className="custom-dropdown">
      <label className="block text-sm font-medium text-[var(--muted-foreground)] mb-1">
        旅行风格
      </label>
      
      <div 
        className="dropdown-button"
        aria-expanded={isOpen}
        onClick={(e) => {
          e.stopPropagation()
          toggle()
        }}
      >
        <div className="flex items-center gap-2">
          <span>{selectedOption.icon}</span>
          <span>{selectedOption.text}</span>
        </div>
        <ChevronDown 
          className={`w-5 h-5 chevron transition-transform ${isOpen ? 'rotate-180' : ''}`} 
        />
      </div>
      
      {isOpen && (
        <div className={`dropdown-options ${isOpen ? 'open' : ''}`}>
          {styleOptions.map((option) => (
            <div
              key={option.value}
              className={`dropdown-option ${option.value === selectedStyle ? 'selected' : ''}`}
              onClick={(e) => {
                e.stopPropagation()
                setStyle(option.value)
              }}
            >
              <span className="text-lg">{option.icon}</span>
              <div>
                <p>{option.text}</p>
                <p className="text-xs text-[var(--muted-foreground)]">
                  {option.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
