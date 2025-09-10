// Travel Agent Pro - Date Picker Hook
// 管理日期选择器的初始化和交互

import { useEffect } from 'react'

declare global {
  interface Window {
    flatpickr: any;
  }
}

export function useDatePicker(isModalOpen: boolean) {
  
  useEffect(() => {
    // 加载外部资源
    const loadExternalResources = () => {
      // 加载 Flatpickr CSS
      if (!document.querySelector('link[href*="flatpickr"]')) {
        const flatpickrCSS = document.createElement('link')
        flatpickrCSS.rel = 'stylesheet'
        flatpickrCSS.href = 'https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css'
        document.head.appendChild(flatpickrCSS)
      }

      // 加载 Flatpickr JS
      if (!window.flatpickr) {
        const flatpickrScript = document.createElement('script')
        flatpickrScript.src = 'https://cdn.jsdelivr.net/npm/flatpickr'
        flatpickrScript.onload = () => {
          // 加载中文语言包
          const localeScript = document.createElement('script')
          localeScript.src = 'https://npmcdn.com/flatpickr/dist/l10n/zh.js'
          localeScript.onload = initializeFlatpickr
          document.head.appendChild(localeScript)
        }
        document.head.appendChild(flatpickrScript)
      } else {
        initializeFlatpickr()
      }
    }

    const initializeFlatpickr = () => {
      if (isModalOpen && window.flatpickr) {
        setTimeout(() => {
          const dateInput = document.getElementById('date-picker')
          if (dateInput && !dateInput.classList.contains('flatpickr-input')) {
            // 设置中文本地化
            if (window.flatpickr.l10ns && window.flatpickr.l10ns.zh) {
              window.flatpickr.localize(window.flatpickr.l10ns.zh)
            }
            
            window.flatpickr("#date-picker", {
              mode: "range",
              dateFormat: "Y-m-d",
              locale: "zh",
              monthSelectorType: "dropdown",
              showMonths: 2,
              disableMobile: true,
              appendTo: document.body,
              minDate: "today", // 限制不能选择过去的日期
              onReady: (selectedDates: any, dateStr: string, instance: any) => {
                instance.calendarContainer.classList.add('dark')
              }
            })
          }
        }, 100)
      }
    }

    loadExternalResources()
  }, [isModalOpen])

  // 获取日期选择器的值
  const getDateRange = () => {
    const dateInput = document.getElementById('date-picker') as HTMLInputElement
    const dateRange = dateInput?.value
    
    console.log('📅 Date input element:', dateInput)
    console.log('📅 Date input value:', dateRange) // 调试日志
    
    if (!dateRange) {
      return {
        startDate: '',
        durationDays: 2
      }
    }
    
    // 尝试不同的分隔符格式
    let start = '', end = ''
    if (dateRange.includes(' to ')) {
      [start, end] = dateRange.split(' to ')
    } else if (dateRange.includes(' 至 ')) {
      [start, end] = dateRange.split(' 至 ')
    } else if (dateRange.includes(' - ')) {
      [start, end] = dateRange.split(' - ')
    } else {
      // 如果只选择了一个日期，就当作开始日期
      start = dateRange
      end = dateRange
    }
    
    if (!start || !end) {
      return {
        startDate: '',
        durationDays: 2
      }
    }
    
    const startDate = start.trim()
    const startDateObj = new Date(start.trim())
    const endDateObj = new Date(end.trim())
    const durationDays = Math.ceil(
      (endDateObj.getTime() - startDateObj.getTime()) / (1000 * 60 * 60 * 24)
    ) + 1
    
    console.log('📅 Parsed dates:', { startDate, durationDays }) // 调试日志
    
    return {
      startDate,
      durationDays
    }
  }

  return {
    getDateRange
  }
}


