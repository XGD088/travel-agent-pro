'use client'

import React, { useState, useEffect } from 'react'
import { Edit3, Map, Download, Share2, X, ChevronDown, RefreshCw, Rocket } from 'lucide-react'

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

interface Plan {
  city: string
}

export default function Home() {
  // App State - 核心状态管理
  const [appState, setAppState] = useState<{ plan: Plan | null }>({ plan: null })
  
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
  const hasPlan = !!appState.plan

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

  const handleSubmit = () => {
    // Mock plan data - 后续替换为真实API调用
    setAppState({ plan: { city: '北京' } })
    closeModal()
  }

  // 根据状态渲染侧边栏详情
  const renderPlanDetails = () => {
    if (!hasPlan) {
      return <p className="text-sm text-muted-foreground">当前没有行程，点击下方按钮开始您的第一次规划。</p>
    }
    
    return (
      <div>
        <label className="text-sm font-medium text-muted-foreground">目的地</label>
        <p className="text-base font-semibold text-foreground mt-1">{appState.plan?.city}</p>
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
        </div>
      )
    }

    return (
      <>
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-foreground">您的{appState.plan?.city}之旅</h1>
            <p className="text-muted-foreground mt-1">已为您智能优化</p>
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
        <div className="card p-5">
          <p>行程 for {appState.plan?.city} will be here.</p>
        </div>
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
                className="py-2 px-5 bg-[var(--secondary)] text-[var(--secondary-foreground)] rounded-md font-semibold hover:bg-[var(--accent)]"
              >
                取消
              </button>
              <button 
                onClick={handleSubmit}
                className="py-2 px-5 btn-primary flex items-center gap-2"
              >
                {hasPlan ? (
                  <RefreshCw className="w-4 h-4" />
                ) : (
                  <Rocket className="w-4 h-4" />
                )}
                <span>{hasPlan ? "更新行程" : "生成行程"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}