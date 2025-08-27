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
    
    if (!dateRange || !dateRange.includes(' to ')) {
      return {
        startDate: '',
        durationDays: 2
      }
    }
    
    const [start, end] = dateRange.split(' to ')
    const startDate = start.trim()
    const startDateObj = new Date(start)
    const endDateObj = new Date(end)
    const durationDays = Math.ceil(
      (endDateObj.getTime() - startDateObj.getTime()) / (1000 * 60 * 60 * 24)
    ) + 1
    
    return {
      startDate,
      durationDays
    }
  }

  return {
    getDateRange
  }
}
