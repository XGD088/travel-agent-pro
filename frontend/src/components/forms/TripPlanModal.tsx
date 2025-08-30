// Travel Agent Pro - Trip Plan Modal Component
// 行程规划模态框组件

import React from 'react'
import { RefreshCw, Rocket, Loader2, AlertCircle } from 'lucide-react'
import { Modal, ModalFooter } from '../ui/Modal'
import { Button } from '../ui/Button'
import { DatePicker } from './DatePicker'
import { StyleDropdown } from './StyleDropdown'
import { TagInput } from './TagInput'
import { useModal, useFormState, useStyleDropdown } from '../../stores/uiStore'
import { useTripStore, useTripPlan, useTripLoading, useTripError } from '../../stores/tripStore'
import { useDatePicker } from '../../hooks/useDatePicker'
import { TripRequest } from '../../lib/api'

export function TripPlanModal() {
  const { isOpen, close } = useModal()
  const { selectedStyle } = useStyleDropdown()
  const { tags, specialRequirement, setSpecialRequirement } = useFormState()
  const { generateTrip, clearError } = useTripStore()
  const tripPlan = useTripPlan()
  const isLoading = useTripLoading()
  const error = useTripError()
  const { getDateRange } = useDatePicker(isOpen)
  
  const hasPlan = !!tripPlan

  const handleSubmit = async () => {
    clearError()
    
    try {
      // 获取日期范围
      const { startDate, durationDays } = getDateRange()
      
      // 构建请求
      const request: TripRequest = {
        destination: '北京', // 暂时固定，后续可以从表单获取
        duration_days: durationDays,
        theme: selectedStyle, // 使用选择的旅行风格
        interests: tags.map(tag => tag.text), // 使用标签作为兴趣
        start_date: startDate || undefined,
        include_accommodation: false, // 根据需要调整
      }
      
      // 如果有特殊要求，添加到主题中
      if (specialRequirement.trim()) {
        request.theme = `${request.theme} - ${specialRequirement.trim()}`
      }

      await generateTrip(request)
      close()
      
    } catch (err) {
      // 错误已经在store中处理
      console.error('❌ 行程规划失败:', err)
    }
  }

  const getStyleText = (style: string) => {
    const styleMap: Record<string, string> = {
      'relaxed': '轻松',
      'packed': '紧凑', 
      'business': '商务'
    }
    return styleMap[style] || style
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={close}
      title={hasPlan ? "优化您的北京之旅" : "创建您的北京之旅"}
      description="调整下方参数，AI 将为您重新生成更合心意的行程。"
    >
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 日期选择器 */}
          <DatePicker />
          
          {/* 风格下拉框 */}
          <StyleDropdown />
        </div>
        
        {/* 特殊要求 */}
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
        
        {/* 标签输入 */}
        <TagInput />
      </div>
      
      <ModalFooter>
        <Button 
          variant="secondary"
          onClick={close}
          disabled={isLoading}
        >
          取消
        </Button>
        <Button 
          onClick={handleSubmit}
          disabled={isLoading}
          isLoading={isLoading}
          icon={
            isLoading ? undefined : 
            hasPlan ? <RefreshCw className="w-4 h-4" /> : 
            <Rocket className="w-4 h-4" />
          }
        >
          {isLoading ? "生成中..." : hasPlan ? "更新行程" : "生成行程"}
        </Button>
      </ModalFooter>
      
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
    </Modal>
  )
}

