// Travel Agent Pro - Trip State Management
// 使用 Zustand 管理行程相关状态

import { create } from 'zustand'
import { TripPlan, TripRequest, api, formatAPIError } from '../lib/api'

interface TripState {
  // 状态
  tripPlan: TripPlan | null
  isLoading: boolean
  error: string | null
  
  // 操作
  generateTrip: (request: TripRequest) => Promise<void>
  setTripPlan: (plan: TripPlan | null) => void
  clearError: () => void
  setLoading: (loading: boolean) => void
}

export const useTripStore = create<TripState>((set, get) => ({
  // 初始状态
  tripPlan: null,
  isLoading: false,
  error: null,
  
  // 生成行程
  generateTrip: async (request: TripRequest) => {
    set({ isLoading: true, error: null })
    
    try {
      console.log('🚀 发送行程规划请求:', request)
      const plan = await api.planWithGraph(request)
      
      set({ 
        tripPlan: plan, 
        isLoading: false,
        error: null 
      })
      
      console.log('✅ 行程规划生成成功:', plan)
    } catch (err) {
      const errorMessage = formatAPIError(err)
      set({ 
        error: errorMessage, 
        isLoading: false 
      })
      console.error('❌ 行程规划失败:', err)
    }
  },
  
  // 设置行程
  setTripPlan: (plan: TripPlan | null) => {
    set({ tripPlan: plan })
  },
  
  // 清除错误
  clearError: () => {
    set({ error: null })
  },
  
  // 设置加载状态
  setLoading: (loading: boolean) => {
    set({ isLoading: loading })
  }
}))

// 便捷的选择器函数
export const useTripPlan = () => useTripStore(state => state.tripPlan)
export const useTripLoading = () => useTripStore(state => state.isLoading)
export const useTripError = () => useTripStore(state => state.error)
