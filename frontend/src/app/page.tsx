'use client'

import React, { useState, useEffect } from 'react'
import { Edit3, Map, Download, Share2, X, ChevronDown, RefreshCw, Rocket, Loader2, AlertCircle } from 'lucide-react'
import { api, TripRequest, TripPlan, formatAPIError, checkBackendHealth } from '../lib/api'

declare global {
  interface Window {
    flatpickr: any;
  }
}

interface StyleOption {
  value: string
  icon: string
  text: string
  description: string
  selected?: boolean
}

interface Tag {
  id: number
  text: string
  type: 'system' | 'custom'
}

export default function Home() {
  // App State - 核心状态管理
  const [tripPlan, setTripPlan] = useState<TripPlan | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null)
  
  // Modal and UI state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isStyleDropdownOpen, setIsStyleDropdownOpen] = useState(false)
  
  // Form state
  const [styleOptions, setStyleOptions] = useState<StyleOption[]>([
    { value: 'relaxed', icon: '🧘', text: '轻松', description: '每日2-3个活动', selected: true },
    { value: 'packed', icon: '🏃', text: '紧凑', description: '每日4-5个活动' },
    { value: 'business', icon: '👔', text: '商务', description: '高效、含会议时间' }
  ])
  const [tags, setTags] = useState<Tag[]>([
    { id: 1, text: '亲子', type: 'system' },
    { id: 2, text: '避免博物馆', type: 'custom' }
  ])
  const [tagInput, setTagInput] = useState('')
  const [specialRequirement, setSpecialRequirement] = useState('')

  const selectedStyle = styleOptions.find(opt => opt.selected) || styleOptions[0]
  const hasPlan = !!tripPlan

  // 检查后端服务状态
  useEffect(() => {
    checkBackendHealth().then(setBackendHealthy);
  }, []);

  useEffect(() => {
    // Load external scripts and styles (暗色主题现在是默认的)
    const loadExternalResources = () => {
      // Load Flatpickr CSS
      if (!document.querySelector('link[href*="flatpickr"]')) {
        const flatpickrCSS = document.createElement('link')
        flatpickrCSS.rel = 'stylesheet'
        flatpickrCSS.href = 'https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css'
        document.head.appendChild(flatpickrCSS)
      }

      // 主题CSS已经在layout.tsx中预加载了

      // Load Flatpickr JS
      if (!window.flatpickr) {
        const flatpickrScript = document.createElement('script')
        flatpickrScript.src = 'https://cdn.jsdelivr.net/npm/flatpickr'
        flatpickrScript.onload = () => {
          // Load Chinese locale
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
            // 采用HTML模板中的flatpickr配置
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

  // Event handlers
  const openModal = () => {
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
  }

  const handleStyleSelect = (selectedValue: string) => {
    setStyleOptions(prev => 
      prev.map(opt => ({ ...opt, selected: opt.value === selectedValue }))
    )
    setIsStyleDropdownOpen(false)
  }

  // 处理点击外部关闭下拉菜单 (类似HTML模板中的逻辑)
  useEffect(() => {
    const handleDocumentClick = () => {
      setIsStyleDropdownOpen(false)
    }

    if (isStyleDropdownOpen) {
      document.addEventListener('click', handleDocumentClick)
      return () => document.removeEventListener('click', handleDocumentClick)
    }
  }, [isStyleDropdownOpen])

  const handleTagInputKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault()
      const newTag: Tag = {
        id: Date.now(),
        text: tagInput.trim(),
        type: 'custom'
      }
      setTags([...tags, newTag])
      setTagInput('')
    }
  }

  const removeTag = (tagId: number) => {
    setTags(tags.filter(tag => tag.id !== tagId))
  }

  const handleSubmit = async () => {
    setError(null);
    setIsLoading(true);
    
    try {
      // 获取日期选择器的值
      const dateInput = document.getElementById('date-picker') as HTMLInputElement;
      const dateRange = dateInput?.value;
      
      // 解析日期范围 (格式: "2025-09-06 to 2025-09-07")
      let startDate = '';
      let durationDays = 2; // 默认值
      
      if (dateRange && dateRange.includes(' to ')) {
        const [start, end] = dateRange.split(' to ');
        startDate = start.trim();
        const startDateObj = new Date(start);
        const endDateObj = new Date(end);
        durationDays = Math.ceil((endDateObj.getTime() - startDateObj.getTime()) / (1000 * 60 * 60 * 24)) + 1;
      }
      
      // 构建请求
      const request: TripRequest = {
        destination: '北京', // 暂时固定，后续可以从表单获取
        duration_days: durationDays,
        theme: selectedStyle.text, // 使用选择的旅行风格
        interests: tags.map(tag => tag.text), // 使用标签作为兴趣
        start_date: startDate || undefined,
        include_accommodation: false, // 根据需要调整
      };
      
      // 如果有特殊要求，添加到主题中
      if (specialRequirement.trim()) {
        request.theme = `${request.theme} - ${specialRequirement.trim()}`;
      }

      console.log('🚀 发送行程规划请求:', request);
      
      const plan = await api.planWithGraph(request);
      
      setTripPlan(plan);
      closeModal();
      
      console.log('✅ 行程规划生成成功:', plan);
      
    } catch (err) {
      const errorMessage = formatAPIError(err);
      setError(errorMessage);
      console.error('❌ 行程规划失败:', err);
    } finally {
      setIsLoading(false);
    }
  }

  // 根据状态渲染侧边栏详情
  const renderPlanDetails = () => {
    if (!hasPlan) {
      return <p className="text-sm text-muted-foreground">当前没有行程，点击下方按钮开始您的第一次规划。</p>
    }
    
    return (
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium text-muted-foreground">目的地</label>
          <p className="text-base font-semibold text-foreground mt-1">{tripPlan?.destination}</p>
        </div>
        
        <div>
          <label className="text-sm font-medium text-muted-foreground">日期</label>
          <p className="text-base font-semibold text-foreground mt-1">
            {tripPlan?.start_date} - {tripPlan?.end_date}
          </p>
        </div>
        
        <div>
          <label className="text-sm font-medium text-muted-foreground">旅行主题</label>
          <p className="text-base font-semibold text-foreground mt-1">{tripPlan?.theme}</p>
        </div>
        
        <div>
          <label className="text-sm font-medium text-muted-foreground">总预算</label>
          <p className="text-base font-semibold text-foreground mt-1">
            约 ¥{tripPlan?.total_estimated_cost}
          </p>
        </div>
      </div>
    )
  }

  // 根据状态渲染主内容
  const renderMainContent = () => {
    if (!hasPlan) {
      return (
        <div className="text-center py-24 flex flex-col items-center">
          <Map className="w-16 h-16 text-muted-foreground" />
          <h2 className="text-2xl font-semibold mt-4">无行程</h2>
          <p className="mt-2 text-muted-foreground">请点击左侧的"新建行程"按钮开始。</p>
          
          {/* 显示后端连接状态 */}
          {backendHealthy === false && (
            <div className="mt-6 p-4 bg-red-100 border border-red-300 rounded-lg text-red-700">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                <p>后端服务连接失败，请确保后端服务正在运行 (http://localhost:8000)</p>
              </div>
            </div>
          )}
        </div>
      )
    }

    return (
      <>
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-foreground">您的{tripPlan?.destination}之旅</h1>
            <p className="text-muted-foreground mt-1">已为您智能优化 · {tripPlan?.duration_days}天行程</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="btn-secondary border border-border flex items-center gap-2 py-2 px-4 rounded-lg font-semibold shadow-sm">
              <Download className="w-4 h-4" />
              <span>导出</span>
            </button>
            <button className="btn-secondary border border-border flex items-center gap-2 py-2 px-4 rounded-lg font-semibold shadow-sm">
              <Share2 className="w-4 h-4" />
              <span>分享</span>
            </button>
          </div>
        </header>
        
        {/* 行程总览 */}
        {tripPlan?.plan_rationale && (
          <div className="card p-5 mb-6">
            <h3 className="text-lg font-semibold mb-3">规划思路</h3>
            <p className="text-muted-foreground">{tripPlan.plan_rationale}</p>
          </div>
        )}
        
        {/* 每日行程 */}
        <div className="space-y-6">
          {tripPlan?.daily_plans.map((dayPlan, index) => (
            <div key={dayPlan.date} className="card p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-foreground">
                    第{index + 1}天 · {dayPlan.day_title}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1">{dayPlan.date}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">当日预算</p>
                  <p className="font-semibold text-foreground">¥{dayPlan.estimated_daily_cost}</p>
                </div>
              </div>
              
              {/* 活动列表 */}
              <div className="space-y-4 mb-4">
                {dayPlan.activities.map((activity, actIndex) => (
                  <div key={actIndex} className="flex gap-4 p-4 bg-[var(--muted)] rounded-lg">
                    <div className="flex-shrink-0 text-center">
                      <div className="w-12 h-12 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-full flex items-center justify-center font-semibold">
                        {actIndex + 1}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {activity.start_time}
                      </p>
                    </div>
                    
                    <div className="flex-grow">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-foreground">{activity.name}</h4>
                        {activity.estimated_cost && (
                          <span className="text-sm text-muted-foreground">¥{activity.estimated_cost}</span>
                        )}
                      </div>
                      
                      <p className="text-sm text-muted-foreground mb-1">{activity.location}</p>
                      <p className="text-sm text-foreground mb-2">{activity.description}</p>
                      
                      <div className="flex flex-wrap gap-2 text-xs">
                        <span className="px-2 py-1 bg-[var(--secondary)] text-[var(--secondary-foreground)] rounded">
                          {activity.type}
                        </span>
                        <span className="px-2 py-1 bg-[var(--accent)] text-[var(--accent-foreground)] rounded">
                          {activity.duration_minutes}分钟
                        </span>
                        {activity.start_time && activity.end_time && (
                          <span className="px-2 py-1 bg-[var(--accent)] text-[var(--accent-foreground)] rounded">
                            {activity.start_time} - {activity.end_time}
                          </span>
                        )}
                      </div>
                      
                      {activity.tips && (
                        <p className="text-xs text-muted-foreground mt-2">💡 {activity.tips}</p>
                      )}
                      
                      {activity.replacement_reason && (
                        <p className="text-xs text-orange-600 mt-2">🔄 {activity.replacement_reason}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              
              {/* 当日总结 */}
              <div className="pt-4 border-t border-[var(--border)]">
                <p className="text-sm text-muted-foreground">{dayPlan.daily_summary}</p>
              </div>
            </div>
          ))}
        </div>
        
        {/* 总体建议 */}
        {tripPlan?.general_tips && tripPlan.general_tips.length > 0 && (
          <div className="card p-5 mt-6">
            <h3 className="text-lg font-semibold mb-3">出行建议</h3>
            <ul className="space-y-2">
              {tripPlan.general_tips.map((tip, index) => (
                <li key={index} className="flex items-start gap-2 text-sm">
                  <span className="text-[var(--primary)] mt-1">•</span>
                  <span className="text-muted-foreground">{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </>
    )
  }

  return (
    <>
      <div className="flex min-h-screen">
        {/* Sidebar - 采用HTML模板的结构 */}
        <aside className="w-1/3 lg:w-1/4 bg-[var(--sidebar)] p-8 border-r border-[var(--sidebar-border)] flex flex-col gap-8">
          <div>
            <h1 className="text-2xl font-bold text-[var(--foreground)]">Travel Agent Pro</h1>
            <p className="text-sm text-[var(--muted-foreground)] mt-1">您的智能行程规划助手</p>
          </div>
          
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-[var(--foreground)]">您的计划</h2>
            <div id="plan-details-container">
              {renderPlanDetails()}
            </div>
          </div>
          
          <div className="mt-auto space-y-3">
            <button 
              onClick={openModal}
              className="w-full btn-primary flex items-center justify-center gap-2 text-lg py-3"
            >
              {hasPlan ? (
                <Edit3 className="w-5 h-5" />
              ) : (
                <Rocket className="w-5 h-5" />
              )}
              <span>{hasPlan ? "优化行程" : "新建行程"}</span>
            </button>
          </div>
        </aside>

        {/* Main Content - 采用HTML模板的结构 */}
        <main className="w-2/3 lg:w-3/4 p-8 lg:p-12">
          <div id="main-content-container">
            {renderMainContent()}
          </div>
        </main>
      </div>

      {/* Modal - 采用HTML模板的结构和样式 */}
      {isModalOpen && (
        <div 
          className={`modal-overlay ${isModalOpen ? 'active' : ''}`}
          onClick={(e) => e.target === e.currentTarget && closeModal()}
        >
          <div className="modal-content">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-2xl font-bold">
                {hasPlan ? "优化您的北京之旅" : "创建您的北京之旅"}
              </h2>
              <button 
                onClick={closeModal}
                className="text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <p className="text-[var(--muted-foreground)] mb-6">
              调整下方参数，AI 将为您重新生成更合心意的行程。
            </p>
            
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Date Picker */}
                <div>
                  <label className="block text-sm font-medium text-[var(--muted-foreground)] mb-1">
                    日期范围
                  </label>
                  <input 
                    id="date-picker" 
                    type="text" 
                    placeholder="选择您的旅行日期" 
                    className="w-full p-2 bg-[var(--input)] border border-[var(--border)] rounded-md cursor-pointer"
                  />
                </div>
                
                {/* Style Dropdown */}
                <div className="custom-dropdown">
                  <label className="block text-sm font-medium text-[var(--muted-foreground)] mb-1">
                    旅行风格
                  </label>
                  <div 
                    className="dropdown-button"
                    aria-expanded={isStyleDropdownOpen}
                    onClick={(e) => {
                      e.stopPropagation()
                      setIsStyleDropdownOpen(!isStyleDropdownOpen)
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <span>{selectedStyle.icon}</span>
                      <span>{selectedStyle.text}</span>
                    </div>
                    <ChevronDown className={`w-5 h-5 chevron transition-transform ${isStyleDropdownOpen ? 'rotate-180' : ''}`} />
                  </div>
                  
                  {isStyleDropdownOpen && (
                    <div className={`dropdown-options ${isStyleDropdownOpen ? 'open' : ''}`}>
                      {styleOptions.map((option) => (
                        <div
                          key={option.value}
                          className={`dropdown-option ${option.selected ? 'selected' : ''}`}
                          onClick={(e) => {
                            e.stopPropagation()
                            handleStyleSelect(option.value)
                          }}
                        >
                          <span className="text-lg">{option.icon}</span>
                          <div>
                            <p>{option.text}</p>
                            <p className="text-xs text-[var(--muted-foreground)]">{option.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              
              {/* Special Requirements */}
              <div>
                <label className="block text-sm font-medium text-[var(--muted-foreground)] mb-1">
                  特殊要求 (选填)
                </label>
                <input 
                  type="text" 
                  value={specialRequirement}
                  onChange={(e) => setSpecialRequirement(e.target.value)}
                  placeholder="例如：希望能去一家评价好的烤鸭店..." 
                  className="w-full p-2 bg-[var(--input)] border border-[var(--border)] rounded-md"
                />
              </div>
              
              {/* Tags */}
              <div>
                <label className="block text-sm font-medium text-[var(--muted-foreground)] mb-2">
                  智能必去清单
                </label>
                <div className="tag-input-container">
                  {tags.map((tag) => (
                    <span
                      key={tag.id}
                      className={`tag ${tag.type}`}
                    >
                      {tag.text}
                      <button 
                        onClick={() => removeTag(tag.id)}
                        className="tag-remove"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={handleTagInputKeyPress}
                    placeholder="输入想去的地方后按回车..."
                    className="tag-input"
                  />
                </div>
                <p className="mt-2 text-xs text-[var(--muted-foreground)]">
                  💡 AI将优先满足清单中的安排。
                </p>
              </div>
            </div>
            
            <div className="mt-8 flex justify-end gap-4">
              <button 
                onClick={closeModal}
                disabled={isLoading}
                className="py-2 px-5 bg-[var(--secondary)] text-[var(--secondary-foreground)] rounded-md font-semibold hover:bg-[var(--accent)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                取消
              </button>
              <button 
                onClick={handleSubmit}
                disabled={isLoading}
                className="py-2 px-5 btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : hasPlan ? (
                  <RefreshCw className="w-4 h-4" />
                ) : (
                  <Rocket className="w-4 h-4" />
                )}
                <span>
                  {isLoading ? "生成中..." : hasPlan ? "更新行程" : "生成行程"}
                </span>
              </button>
            </div>
            
            {/* 错误提示 */}
            {error && (
              <div className="mt-4 p-4 bg-red-100 border border-red-300 rounded-lg text-red-700">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold">生成失败</p>
                    <p className="text-sm mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
